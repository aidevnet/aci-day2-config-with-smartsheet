from datetime import datetime
import smartsheet
import json

status_sheet_name = "Status Sheet"

class Status:
    def __init__(self, smartsheet_client, status_sheet):
        self.smartsheet_client = smartsheet_client
        self.status_sheet = self.verify_sheet(status_sheet)

    # Verify ID un status_sheet varible
    def verify_sheet(self, status_sheet):
        """Verifies that status_sheet ID is valid. Creates and safes new ID if status_sheet is invalid."""

        # Check status if status_sheet is default value
        if status_sheet == 0:
            print("[Status Sheet] - Status sheet ID is invalid")
            status_sheet = self.create_sheet()
        else:
            try:
                # Attempt to get sheet
                print("[Status Sheet] - Attempting to find existing status sheet")
                sheet_response = self.smartsheet_client.Sheets.get_sheet(status_sheet)
            except:
                print("[Status Sheet] - Existing status sheet not found")
                status_sheet = self.create_sheet()
            else:
                print("[Status Sheet] - Existing status sheet found")
                
        print("---------------------------------------")
        return(status_sheet)

    # Create new sheet
    def create_sheet(self):
        """Create new Status sheet and return new sheet ID"""
        # Create sheet specifcation
        sheet_spec = smartsheet.models.Sheet({
            "name": status_sheet_name,
            "columns": [{
                "title": "Date",
                "type": "TEXT_NUMBER",
                "primary": True
            }, {
                "title": "Status",
                "type": "TEXT_NUMBER"
            }, {
                "title": "Description",
                "type": "TEXT_NUMBER"
            }]
        })

        # Send request to create new sheet
        response = self.smartsheet_client.Home.create_sheet(sheet_spec)
        new_sheet = response.result.id
        print(f"[Status Sheet] - Created new status sheet with ID of {new_sheet}")

        # Get config from file
        with open("./config.json", mode="r+") as json_file:
            configuration = json.load(json_file)

        # Update config
        configuration["status_sheet"] = new_sheet

        # Save config to file
        with open("./config.json", mode="w") as json_file:
            json.dump(configuration, json_file, ensure_ascii=False, indent=2)

        return(new_sheet)

    # Send process status to sheet
    def send_update(self, response):
        """Send process status update to the status sheet."""
        sheet_response = self.smartsheet_client.Sheets.get_sheet(self.status_sheet)

        # Get date to add time stamp to update
        date = datetime.now()

        # Get Status sheet columns
        columns = []
        for column in sheet_response.columns:
            columns.append(column.id)

        # Create new row
        new_row = smartsheet.models.Row()
        new_row.to_top = True
        new_row.cells.append({'column_id': columns[0],'value': date.strftime("%x, %X")})
        new_row.cells.append({'column_id': columns[1],'value': response[0]})
        new_row.cells.append({'column_id': columns[2],'value': response[1]})

        # Add rows to sheet
        response = self.smartsheet_client.Sheets.add_rows(self.status_sheet,[new_row])
        print(f"[Status Update] - Process status sheet updated\n---------------------------------------")
