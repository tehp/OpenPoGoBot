from __future__ import print_function
import time

from six import integer_types
from pgoapi import PGoApi                                           # type: ignore
from pgoapi.exceptions import ServerSideRequestThrottlingException  # type: ignore

from .state_manager import StateManager


class PoGoApi(object):
    def __init__(self, provider="google", username="", password=""):
        self._api = PGoApi()

        self.provider = provider
        self.username = username
        self.password = password

        self.current_position = (0, 0, 0)

        self.state = StateManager()

        self._pending_calls = {}
        self._pending_calls_keys = []

    def login(self):
        try:
            provider, username, password = self.provider, self.username, self.password
            return self._api.login(provider, username, password, app_simulation=True)
        except TypeError:
            return False

    def set_position(self, lat, lng, alt):
        self._api.set_position(lat, lng, alt)

    def get_position(self):
        return self._api.get_position()

    def get_queued_methods(self):
        return self._api.list_curr_methods()

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

    # Wrapper for new PGoApi create_request() function
    def create_request(self):
        return self._api.create_request()

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
                getattr(request, method)(*my_args, **my_kwargs)

            try:
                results = request.call()
            except ServerSideRequestThrottlingException:
                # status code 52: too many requests
                print("[API] Requesting too fast. Retrying in 15 seconds...")
                time.sleep(15)
                continue
            except TypeError:
                print("[API] Failed to perform API call (servers might be offline). Retrying in 15 seconds...")
                time.sleep(15)
                continue

            if results is False or results is None or results.get('status_code', 1) != 1:
                print("[API] API call failed. Retrying in 5 seconds...")
                time.sleep(5)
            else:
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
