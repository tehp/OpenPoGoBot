# Testing

Testing in OpenPoGoBot is performed by the [`pytest`](http://doc.pytest.org/en/latest/), 
[`unittest`](https://docs.python.org/2/library/unittest.html) and 
[`mock`](https://docs.python.org/3/library/unittest.mock.html) python modules. Code coverage is performed by 
[`pytest-cov`](https://pypi.python.org/pypi/pytest-cov).

Testing is run on every build and is required to pass for pull requests.

## Running the tests

```bash
py.test --cov=pokemongo_bot --cov=plugins pokemongo_bot/ plugins/
```

## Writing tests
If you are contributing, we will ask you to write tests for your code. We have developed a test suite that can help you
mocking interaction with the niantic API.

### Testing with the Bot
Almost every functional test will interact with the PGoApi (the python wrapper that calls niantic's api). We have 
created a set of mock generators that can help:

```python
import unittest
from pokemongo_bot.tests import create_mock_bot

class ExampleTest(unittest.TestCase):
    def example_test(self):
        bot = create_mock_bot({
            # Any config values you wish to use for a test
        })
        mocked_pgoapi = bot.api_wrapper._api
        
        mocked_pgoapi.set_response('get_player', {'username': 'test player'})
        
        player = bot.api_wrapper.get_player()
        player.username # 'test player'
        
        # Assert that all the calls have been used
        assert mocked_pgoapi.call_stack_size() == 0
```

For more information, please see [the test class](../pokemongo_bot/tests/__init__.py).

###
