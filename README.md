PostgreSQL Account: mr4217

Application URL: http://35.237.249.212:8111/


Description: 
We implemented the gym manager functionality for the database since this allows us to implement as many functionlities for our database as possible - after all, functionalities available for a gym manager includes all the functionalities a gym customer/ trainer could access. 
The gym manager can see essentially all the entity sets and relations our database has. He can also edit, add, and view as he sees fit. 


Two Interesting pages: 
    Customer "View" page
    Gym "View" page
These pages are compelling because they dynamically aggregate and present rich relational data from multiple tables — providing a comprehensive snapshot of each entity’s connections across the system.

Customer "View" page: This page allows users to view all key information about an individual customer, including their basic profile details and associated gyms, personal trainers, and registered group classes. The page consolidates data across four separate relationships, involving multiple joins and different cardinalities (e.g., many-to-many and one-to-many). It’s essentially a live dashboard for a customer, offering deep insight with a single route and no editing needed. It’s a great example of how normalized data can be presented in a human-friendly way through efficient SQL.
(Note: When the page is loaded, the backend performs multiple read operations: (1) It queries the customers table for basic information. (2) It joins gym_customer_mappings and gyms to retrieve all gyms the customer is linked to. (3) It joins customer_trainer_mappings and trainers to retrieve their assigned personal trainers. (4) It joins customer_group_class_mappings, group_classes, group_class_types, and gyms to show all upcoming or past classes the customer is registered for, including class type and location.)

Similarly and more briefly, for the Gym "View" page: This page allows users to view detailed information about a specific gym — its address, amenities, trainers, and all the group classes that happen there. It showcases multi-dimensional data from several related entities. It uses foreign key relationships across three different join paths, and serves it up in a way that’s readable, concise, and functional for users. It’s particularly interesting because all the information is derived — the gym table itself holds very little of the data shown.


~~~
If attempting to run on your local machine, run using:
```
source .virtualenvs/dbproj/bin/activate
flask run --host=0.0.0.0 --port 8111
```