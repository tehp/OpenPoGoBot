from __future__ import print_function
import time
import random
import jsonpickle

from six import integer_types  # type: ignore
from pgoapi.exceptions import ServerSideRequestThrottlingException, ServerSideAccessForbiddenException, \
    UnexpectedResponseException  # type: ignore
from pgoapi.pgoapi import PGoApi, PGoApiRequest, RpcApi
from pgoapi.protos.POGOProtos.Networking.Requests.RequestType_pb2 import RequestType
from pgoapi.protos.POGOProtos.Networking.Envelopes.Signature_pb2 import Signature
from pgoapi.utilities import get_time

from app import kernel
from .state_manager import StateManager
from .exceptions import AccountBannedException


@kernel.container.register('api_wrapper', ['@pgoapi'], {'provider': '%pogoapi.provider%', 'username': '%pogoapi.username%', 'password': '%pogoapi.password%', 'shared_lib': '%pogoapi.shared_lib%', 'device_info': '%pogoapi.device_info%'})
class PoGoApi(object):
    def __init__(self, api, provider="google", username="", password="", shared_lib="encrypt.dll", device_info=None):
        self._api = api
        self.provider = provider
        self.username = username
        self.password = password

        self.device_info = jsonpickle.decode(device_info)

        self.current_position = (0, 0, 0)

        self.state = StateManager()

        self._pending_calls = {}
        self._pending_calls_keys = []

        self._api.activate_signature(shared_lib)

    def get_api(self):
        return self._api

    def login(self):
        try:
            provider, username, password = self.provider, self.username, self.password
            return self._api.login(provider, username, password, app_simulation=False)
        except TypeError:
            return False

    def set_position(self, lat, lng, alt):
        self._api.set_position(lat, lng, alt)

    def get_position(self):
        return self._api.get_position()

    def get_queued_methods(self):
        return self._api.list_curr_methods()

    def get_player_cache(self):
        return self.state.current_state.get("player", None)

    # Lazily queue RPC functions to be called. These will be filtered later.
    def __getattr__(self, func):
        def function(*args, **kwargs):
            func_name = str(func).upper()
            self._pending_calls[func_name] = (args, kwargs)
            self._pending_calls_keys.append(func_name)
            return self

        return function

    def get_expiration_time(self):
        # pylint: disable=protected-access
        ticket = self._api._auth_provider.get_ticket()
        if ticket is False or ticket is None:
            return 0
        for field in ticket:
            if isinstance(field, integer_types):
                return int(field / 1000 - time.time())
        return 0

    def get_signature(self):
        lat, lng, alt = self.get_position()

        location_fix = [Signature.LocationFix(
            provider='gps',
            timestamp_snapshot=(get_time(ms=True) - RpcApi.START_TIME) - random.randint(100, 300),
            latitude=lat,
            longitude=lng,
            horizontal_accuracy=round(random.uniform(50, 250), 7),
            altitude=alt,
            vertical_accuracy=random.randint(10, 20),
            provider_status=3,
            location_type=1
        )]

        sensor_info = Signature.SensorInfo(
            timestamp_snapshot=(get_time(ms=True) - RpcApi.START_TIME) - random.randint(200, 400),
            magnetometer_x=random.uniform(-0.139084026217, 0.138112977147),
            magnetometer_y=random.uniform(-0.2, 0.19),
            magnetometer_z=random.uniform(-0.2, 0.4),
            angle_normalized_x=random.uniform(-47.149471283, 61.8397789001),
            angle_normalized_y=random.uniform(-47.149471283, 61.8397789001),
            angle_normalized_z=random.uniform(-47.149471283, 5),
            accel_raw_x=random.uniform(0.0729667818829, 0.0729667818829),
            accel_raw_y=random.uniform(-2.788630499244109, 3.0586791383810468),
            accel_raw_z=random.uniform(-0.34825887123552773, 0.19347580173737935),
            gyroscope_raw_x=random.uniform(-0.9703824520111084, 0.8556089401245117),
            gyroscope_raw_y=random.uniform(-1.7470258474349976, 1.4218578338623047),
            gyroscope_raw_z=random.uniform(-0.9681901931762695, 0.8396636843681335),
            accel_normalized_x=random.uniform(-0.31110161542892456, 0.1681540310382843),
            accel_normalized_y=random.uniform(-0.6574847102165222, -0.07290205359458923),
            accel_normalized_z=random.uniform(-0.9943905472755432, -0.7463029026985168),
            accelerometer_axes=3
        )

        activity_status = Signature.ActivityStatus(
            # walking=True,
            # stationary=True,
            # automotive=True,
            # tilting=True
        )
        signature = Signature(
            location_fix=location_fix,
            sensor_info=sensor_info,
            activity_status=activity_status,
            unknown25=-8537042734809897855
        )

        if self.device_info is not None:
            for key in self.device_info:
                setattr(signature.device_info, key, self.device_info[key])

        return signature

    def call(self, ignore_expiration=False, ignore_cache=False):
        methods, method_keys, self._pending_calls, self._pending_calls_keys = self._pending_calls, self._pending_calls_keys, {}, []

        # Check for ticket expiration before continuing
        if self.get_expiration_time() < 60 and ignore_expiration is False:
            print("[API] Token has expired, attempting to log back in...")
            for _ in range(10):
                if self.login() is False:
                    print("[API] Failed to login. Waiting 15 seconds...")
                    time.sleep(15)
            if self.get_expiration_time() < 60 and ignore_expiration is False:
                print("[API] Failed to login after 10 tries, exiting.")
                exit(1)

        # See which methods are uncached
        # If all methods are cached and do not invalidate any states, we can just return current state
        uncached_method_keys = self.state.filter_cached_methods(method_keys) if ignore_cache is False else method_keys
        if len(uncached_method_keys) == 0:
            return self.state.get_state()

        for _ in range(10):

            request = self._api.create_request()

            # build the request
            for method in uncached_method_keys:
                my_args, my_kwargs = methods[method]
                if method == "DOWNLOAD_SETTINGS":
                    dlhash = self.state.get_state().get("dl_settings_hash")
                    if dlhash is not None:
                        my_kwargs["hash"] = dlhash
                getattr(request, method)(*my_args, **my_kwargs)

            # random request delay to prevent status code 52: too many requests
            time.sleep(random.uniform(0.5, 1.5))

            try:
                results = request.call(signature=self.get_signature())
            except ServerSideRequestThrottlingException:
                # status code 52: too many requests
                print("[API] Requesting too fast. Retrying in 10 seconds...")
                time.sleep(10)
                continue
            except ServerSideAccessForbiddenException:
                # 403 Forbidden
                print("[API] Your IP address is most likely banned. Try on a different IP/machine.")
                exit(1)
            except UnexpectedResponseException:
                print("[API] Got a non-200 HTTP response from API. Retrying in 10 seconds...")
                time.sleep(10)
                continue
            except TypeError:
                print("[API] Failed to perform API call (servers might be offline). Retrying in 10 seconds...")
                time.sleep(10)
                continue

            if results is False or results is None:
                print("[API] API call failed (empty response). Retrying in 10 seconds...")
                time.sleep(10)
            else:
                status_code = results.get('status_code', None)
                if status_code == 3:
                    raise AccountBannedException()
                elif status_code != 1:
                    print("[API] API call failed (status code {}). Retrying in 10 seconds...".format(status_code))
                    time.sleep(10)
                    continue

                # status code 1: success
                with open('api-test.txt', 'w') as outfile:
                    outfile.write(str(results))

                self.state.mark_stale(uncached_method_keys)

                # Transform our responses and return our current state
                responses = results.get("responses", {})
                for key in responses:
                    self.state.update_with_response(key, responses[key])

                return self.state.get_state()
        return None
