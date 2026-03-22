# Scrounge API Documentation

## Overview

The Scrounge API provides RESTful access to user inventory data. All endpoints are grouped under the `/api/v1/` prefix and require user authentication.

## Base URL
```
http://your-domain.com/api/v1/
```

## Authentication

All API endpoints require user authentication. The API uses session-based authentication - you must be logged in through the web interface to access API endpoints.

### Authentication Error Response
```json
{
  "error": "Authentication required"
}
```
**Status Code:** `401 Unauthorized`

## Endpoints

### 1. Get All Inventory Items

Retrieve a list of all inventory items for the authenticated user.

**Endpoint:** `GET /api/v1/inventory`

**Authentication:** Required

**Response (Success):**
```json
{
  "success": true,
  "count": 2,
  "items": [
    {
      "name": "apple",
      "quantity": "5 pieces"
    },
    {
      "name": "bread",
      "quantity": "2 loaves"
    }
  ]
}
```
**Status Code:** `200 OK`

**Response (Empty Inventory):**
```json
{
  "success": true,
  "count": 0,
  "items": []
}
```
**Status Code:** `200 OK`

### 2. Get Specific Inventory Item

Retrieve details for a specific inventory item by name.

**Endpoint:** `GET /api/v1/inventory/{item_name}`

**Authentication:** Required

**Parameters:**
- `item_name` (string): The name of the inventory item (URL-encoded)

**Example Request:**
```
GET /api/v1/inventory/apple
```

**Response (Success):**
```json
{
  "success": true,
  "item": {
    "name": "apple",
    "quantity": "5 pieces"
  }
}
```
**Status Code:** `200 OK`

**Response (Item Not Found):**
```json
{
  "success": false,
  "error": "Item \"apple\" not found"
}
```
**Status Code:** `404 Not Found`

## Error Responses

### 401 Unauthorized
Returned when attempting to access API endpoints without authentication.

```json
{
  "error": "Authentication required"
}
```

### 404 Not Found
Returned when requesting a specific item that doesn't exist for the authenticated user.

```json
{
  "success": false,
  "error": "Item \"item_name\" not found"
}
```

### 500 Internal Server Error
Returned when an unexpected server error occurs.

```json
{
  "success": false,
  "error": "Failed to retrieve inventory"
}
```

## Data Security

- All inventory data is encrypted at rest using Fernet encryption
- Users can only access their own inventory items (user-scoped data)
- Session-based authentication ensures secure access control

## Content Types

- **Request:** Not applicable (GET endpoints only)
- **Response:** `application/json`

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Testing

A comprehensive test script `test_api.py` is included to verify API functionality:

```bash
python test_api.py
```

The test script will:
- Test unauthenticated access (should return 401)
- Register a test user
- Login and test authenticated access
- Add inventory items and verify API responses
- Test 404 responses for non-existent items

## Example Usage

### Python with requests library:

```python
import requests

# Create a session to maintain authentication
session = requests.Session()

# Login through web interface first, then use the session
# The session will maintain cookies for API access

# Get all inventory items
response = session.get('http://localhost:5000/api/v1/inventory')
inventory_data = response.json()

# Get specific item
response = session.get('http://localhost:5000/api/v1/inventory/apple')
item_data = response.json()
```

### JavaScript with fetch:

```javascript
// Assuming you have a valid session cookie

// Get all inventory items
fetch('/api/v1/inventory')
  .then(response => response.json())
  .then(data => {
    console.log('Inventory:', data);
  });

// Get specific item
fetch('/api/v1/inventory/apple')
  .then(response => response.json())
  .then(data => {
    console.log('Apple item:', data);
  });
```

## Future Enhancements

Potential future API endpoints could include:
- `POST /api/v1/inventory` - Add new inventory items
- `PUT /api/v1/inventory/{item_name}` - Update existing items
- `DELETE /api/v1/inventory/{item_name}` - Remove items
- `GET /api/v1/recipes` - Access user recipes
- `GET /api/v1/preferences` - Get user cuisine preferences

## Versioning

The API uses URL-based versioning (`/api/v1/`). Future versions will use `/api/v2/`, etc.

## Support

For API-related issues or questions, refer to the main application documentation or contact the development team.