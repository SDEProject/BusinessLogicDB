# BusinessLogicDB
The Business Logic DB layer manages all operations requested by the user related to the internal database.
More in details, it parses the HTTP requests in order to understand the user's intention. 
For instance, the user can request the information about the first hotel saved in the results table, 
so the Business Logic DB parses the HTTP request and it understands that 
it must retrieve the information in the results table contacting the DB Data layer, 
then it filters the results for hotel type and takes the first one.

The information about the API are available in the [Wiki page](https://github.com/SDEProject/BusinessLogicDB/wiki).
The service is running at [business-logic-db-layer.herokuapp.com](https://business-logic-db-layer.herokuapp.com).

You can test Travelando project using [Travelando bot](http://t.me/TravelandoBot). 

The bot is able to understand the following sentences:

**Search**
* Select the hotels in [Trento] where you can check-in [at 14.30 o'clock].
* Get the [easiest] mountain path [without equipment required].
* Give me the position of the [bike] shops.
* Give me the list of [local traditional] shops in [Alto Adige].

**Save**
* Can you please save the [search]?
* Can you please save the [first] result?
* Save the [search]
* Save the [first] result

**Retrieve**
* Give me all [results]
* Give me the [first] result
* Give me the [hotel] result
* Give me the [first] [hotel] result
* Give me the [local traditional] shop results
* Give me the [first] [local traditional] shop result
* Give me the mountain path results with [easy] as difficulty

**Delete**
* Delete all [results]
* Delete the [first] result
* Delete the [hotel] result
* Delete the [first] [hotel] result
* Delete the [local traditional] shop results
* Delete the [first] [local traditional] shop result
* Delete the mountain path results with [easy] as difficulty
* Delete the [result] with id [1]

_Note: you can sobstitute all word in the square brackets with other values_
