# Carputer

The carputer is a Raspberry Pi-based telemetry recorder for my car. It collects GPS, speed, and fuel economy data and writes them to a small OLED screen.

Data is taken from a USB OBD-II dongle (bluetooth proved to be too unreliable) and a u-blox neo6mv2 GPS module. The Pi was originally an old-fashoned model B, but I've upgraded to a Zero because holy cow, pretty cool, right? The package is powered from a [Mausberry Circuits car switch](http://mausberry-circuits.myshopify.com/collections/car-power-supply-switches/products/2a-car-supply-switch).

It's been through a few revisions and has worked, not worked, worked, and is currently almost working. I'll create a more comprehensive writeup once it's in working order again.

Here's version 0.1 in all of its gnarly glory:
![Ugly duckling, pre-swan years](http://i.imgur.com/8pkvHiN.jpg)

It looks a bit nicer now; the OLED has better resolution, and there are fewer wires jutting out of it.
