# form-creator-server

An app for creating simple forms.

Endpoints:
- `/` - home page;
- `form-creator/create/` - create new form here;
- `form-creator/data/<form-uid>/` - show submitted data for a form with given UID.

JSON RPC endpoints:
- `api/form/`
  - `get_form` - returns empty form with provided UID

     Request example:
 
        {
          "jsonrpc": "2.0",
          "id": "0",
          "method": "get_form",
          "params": {
            "form_uid": "9244cba0-8f67-463e-b9ce-2b07ddbbf950"
          }
        }

  - `post_form` - submit a form
  
     Request example:
        
        {
          "jsonrpc": "2.0",
          "id": "0",
          "method": "post_form",
          "params": {
            "form_uid": "9244cba0-8f67-463e-b9ce-2b07ddbbf950",
            "form_data": {
              "s1": "2",
              "s2": "a"
            }
          }
        }
        
  - `get_form_data` - get submitted data for given form
  
     Request example:
        
        {
          "jsonrpc": "2.0",
          "id": "0",
          "method": "get_form_data",
          "params": {
            "form_uid": "4ae41c41-98ae-4107-bc76-c519fd9ace27"
          }
        }
