refactor to create projects and give ashaID at project level
and save devices based on project ID

NOTES

# every day at 6am

scheduler.add_job(my_function, 'cron', hour=6, minute=0)

# every Friday at 9pm

scheduler.add_job(my_function, 'cron', day_of_week='fri', hour=21)

# every weekday at 8am

scheduler.add_job(my_function, 'cron', day_of_week='mon-fri', hour=8)

# every 30 minutes

scheduler.add_job(my_function, 'cron', minute='\*/30')

from datetime import datetime

# run once on a specific date

scheduler.add_job(my_function, 'date',
run_date=datetime(2026, 5, 10, 6, 0, 0))

---

│ │ │ │ │
│ │ │ │ └── day of week (0-7, 0 and 7 = Sunday)
│ │ │ └──── month (1-12)
│ │ └────── day of month (1-31)
│ └──────── hour (0-23)
└────────── minute (0-59)

"0 6 \* \* _" → every day at 6:00am
"0 22 _ \* _" → every day at 10:00pm
"0 6 _ _ 1" → every Monday at 6am
"_/5 \* \* \* _" → every 5 minutes
"0 _/2 \* \* _" → every 2 hours
"0 6 _ _ 1-5" → every weekday at 6am
"0 9 _ _ 5" → every Friday at 9am
"30 7 _ \* \*" → every day at 7:30am
