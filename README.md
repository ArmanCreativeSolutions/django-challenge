# VollyballTicket

The volleyball Federation online ticket selling platform

## Running locally
To run project locally on port 8000, run these commands:

```
pip install -r requirments.txt

cd src

python manage.py migrate
python manage.py runserver

```

It is recommended to use a python virtual environment. 


## Endpoints

### Users App

**POST /users/register/**

- **Description**: Register new user
- **Authentication**: Not required
- **Body**: 
  - `phone_number`
  - `password`
  - `confirm_password`

- **Example Response**:
  ```json
    {
        "message": "User created successfully."
    }
  ```

**POST /users/auth-token/**

- **Description**: Authenticate user
- **Authentication**: Not required
- **Body**: 
  - `phone_number`
  - `password`

- **Example Response**:
  ```json
    {
        "token": "lakdsjlakjflakdsjffjklkadssldka"
    }
  ```

  ### Authentication
    
    User authentication is done by providing a token in the request headers like the following:
    ```
    Authorization: Token lakdsjlakjflakdsjffjklkadssldka
    ``` 

### Matches App

**POST matches/stadium/create/**

- **Description**: Create a stadium
- **Authentication**: Admin user only

- **Example Request**:
  ```json
    {
    "title": "National Stadium",
    "address": "123 Stadium Road, City",
    "lat": 35.6895,
    "long": 51.389
    }
  ```

- **Example Response**:
  ```json
    {
    "id": 1,
    "title": "National Stadium",
    "address": "123 Stadium Road, City",
    "lat": 35.6895,
    "long": 51.389
    }
  ```


**POST matches/seating-arrangement/create/**

- **Description**: Create a seating arrangement for a stadium
- **Authentication**: Admin user only

- **Example Request**:
  ```json
    {
        "stadium": 1,
        "seats": [
            {"column": "A", "row": "1", "section": "North", "pos_x": 10, "pos_y": 20},
            {"column": "A", "row": "2", "section": "North", "pos_x": 15, "pos_y": 25},
            {"column": "B", "row": "1", "section": "South", "pos_x": 20, "pos_y": 30}
        ]
    }
  ```

- **Example Response**:
  ```json
    {
        "id": 2,
        "stadium": 1,
        "seats": [
            {
                "id": 1,
                "column": "A",
                "row": "1",
                "section": "North",
                "pos_x": 10,
                "pos_y": 20
            },
            {
                "id": 2,
                "column": "A",
                "row": "2",
                "section": "North",
                "pos_x": 15,
                "pos_y": 25
            },
            {
                "id": 3,
                "column": "B",
                "row": "1",
                "section": "South",
                "pos_x": 20,
                "pos_y": 30
            }
        ]
    }
  ```


**POST matches/match/create/**

- **Description**: Create a match
- **Authentication**: Admin user only

- **Example Request**:
  ```json
    {
    "stadium": 1,
    "seating_arrangement": 2,
    "team_a": 1,
    "team_b": 2,
    "match_datetime": "2024-12-15T18:30:00Z",
    "tickets": [
        {
            "seat": 1,
            "team": 1,
            "price": 80000
        },
        {
            "seat": 2,
            "team": 2,
            "price": 80000
        },
        {
            "seat": 3,
            "team": null,
            "price": 180000
        }
    ]
    }
  ```

- **Example Response**:
  ```json
    {
        "id": 6,
        "tickets": [
            {
                "id": 13,
                "seat": 1,
                "price": 80000,
                "team": 1
            },
            {
                "id": 14,
                "seat": 2,
                "price": 80000,
                "team": 2
            },
            {
                "id": 15,
                "seat": 3,
                "price": 180000,
                "team": null
            }
        ],
        "match_datetime": "2024-12-15T18:30:00Z",
        "status": 0,
        "team_a": 1,
        "team_b": 2,
        "seating_arrangement": 2
    }
  ```



**PATCH matches/match/<match_id>/publish/**

- **Description**: Publish a match.
- **Authentication**: Admin user only
- **Example Response**:
  ```json
    {
        "message": "Match published successfully"
    }
  ```

  **POST matches/ticket/reserve/**

- **Description**: Reserve tickets to buy
- **Authentication**: Authenticated user only

- **Example Request**:
  ```json
    {
        "ticket_ids": [
            1, 2
        ]
    }
  ```

- **Example Response**:
  ```json
    {
        "id": 2,
        "verification_code": "4539135028",
        "amount": 80000,
        "status": 0,
        "created_at": "2024-12-10T20:16:49.409716Z",
        "buyer": 2
    }
  ```


  **POST matches/ticket-factor/<ticket_factor_id>/finalize/**

- **Description**: Finalize reserved tickets as bought
- **Authentication**: Authenticated user only

- **Example Response**:
  ```json
    {
        "id": 2,
        "verification_code": "4539135028",
        "amount": 80000,
        "status": 1,
        "created_at": "2024-12-10T20:16:49.409716Z",
        "buyer": 2
    }
  ```

## Further Improvements

The project is quite unfinished. I misses many APIs to be a practical ticket selling system. Some of the must important developments are:

1. A periodic task must be developed to free the reserved tickets that has not been paied in a logical time period.
2. Some improvements to serializations and API validations are mentioned in code marked with TODO comments.
3. Response structure of APIs may need change to be practically used by GUI applications.
4. Payments are completely ignored in this implimentation.
