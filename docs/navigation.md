# Navigation Guide

The navigation system in OpenPoGoBot is based on 3 key components:

- A `Navigator`
- A `PathFinder`
- And a `Stepper`

## Navigators
A `Navigator` decides where the bot should go. That is, a latitude, longitude and altitude. 

All `Navigators` extend the [`Navigator`](../pokemongo_bot/navigation/navigator.py) abstract class and must implement a 
`navigate(self, map_cells)` method and `yield`s [`Destination`](../pokemongo_bot/navigation/destination.py) objects
 (if you're not familiar with `generators` and `yield`, [see here](https://wiki.python.org/moin/Generators)).

And that's it! here are a few examples:

- [FortNavigator](../pokemongo_bot/navigation/fort_navigator.py) - Travels to any fort in range
- [WaypointNavigator](../pokemongo_bot/navigation/waypoint_navigator.py) - Travels along a set route
- [CamperNavigator](../pokemongo_bot/navigation/camper_navigator.py) - Camps a single location

## PathFinders
`PathFinders` do just that: they find paths. The bot takes a destination supplied by the `Navigator` and works out how 
to get there. All `PathFinders` extend the [`PathFinder`](../pokemongo_bot/navigation/path_finder/path_finder.py) 
abstract class and must implement a `def path(self, from_lat, form_lng, to_lat, to_lng)` method. The `path` method
must return a list of coordinates the bot must travel to in order to get there. 

> NOTE: The list of coordinates supplied are simply target coordinates. If you start at A and need to travel to C via B,
 your `PathFinder` would return (A, B, C), where A, B and C are the latitude, longitude and altitude coordinates for
 these points

## Stepper
The [`Stepper`](../pokemongo_bot/stepper.py) is responsible for calculating and performing the steps to the points 
supplied by the `PathFinder` in order to reach the `Destination`. The `Stepper` internal to the bot and should not be 
invoked by anything other than the bot. ever.

## How it all ties together
So, here are the steps the bot takes to move your trainer through the word:
```
> bot requests a list destinations from the navigator
    > bot loops each destination and asks stepper to work out all the required steps to get to a destination
        > stepper asks the path finder how to get to the destination and returns a list of steps
    > the bot injects the list of steps into the destination
    > the bot tells the step progress every step
        > after every step, the botter calls fires events of the pokemon and pokestops at the new location
```
