#!/bin/bash

ab -p ab-post-body.txt -T application/json -c 10 -n 2000 http://127.0.0.1:8000/guards/name-case/validate
### Regex July 3rd, 2024 3:53 pm CST - 3:59 pm CST
# Failed requests:        4




# ab -p ab-post-body.txt -T application/json -c 10 -n 2000 http://127.0.0.1:8000/guards/Output%20Guard/validate
### Detect PII and Competitor Check July 3rd, 2024 4:00 pm CST - 4:06 pm CST
# Failed requests:        34