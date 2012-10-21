#pyDupes


> pyDupes is an SQLite3 backed resumeable Duplicate Finder written in Python. It's intended that pyDupes can run on different computers / file servers and achieces this though locally performing hashing operations and sending a small database back to the service host

##To Do

Well, there is a fair bit that needs to be done

- Put together a networking link
- Actually have the setup respond to command line input
- Piece together a cross platform interface (preferably in curses 'cus hey lets be hipster)
- Use multithreading if comparing files on different drives

And probably a mass of other things

##Contribution
I'd love it, and that's why this is here. I'd prefer it you choose to do some development that you regularly use merge requests. Further, can we focus on getting the basics put together - and not worry too much about getting the most efficient code, it needs to be very readible :)

##How to Use
For those who are wanting to use this (in it's current state), you need to have python3 installed. It will not work with python2. However, really, this isn't in a usable state atm :/