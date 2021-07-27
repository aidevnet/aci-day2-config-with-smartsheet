import smartsheet
import json
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

class Initiate:
    def __init__(self):
        self.sheet_ids, self.webhook_name, self.call_back_url, self.smartsheet_access_token, self.status_sheet= self.get_config()
        self.smartsheet_client = self.initialize_client()
        self.webhooks = self.get_webhooks()
        print("---------------------------------------")
        # Interates through sheets in config.
        for sheet_id in self.sheet_ids:
            self.probe_sheet(sheet_id)
            self.initialize_hook(sheet_id)
            print("---------------------------------------")

    # Get set up configuration.
    def get_config(self):
        """Verifies and creates config variable from configuration (config.json) file."""
        # Checks values in config file have been changed.
        if config['Environment']['smartsheet_API_key'] == "" or config['Environment']['sheet_ids'] == [] or config['Environment']['call_back_url'] == "" or config['Environment']['webhook_name'] == "":
            print("---------------------------------------\n[Error] - Make sure you have filled in the configuration fill with your information\n---------------------------------------")
        else:
            print("[Initialize] - configuration file variable located")
            sheets = list(map(int, config['Environment']['sheet_ids'].split(',')))
            return (sheets, config["Environment"]["webhook_name"], config["Environment"]["call_back_url"], config["Environment"]["smartsheet_API_key"], config["Environment"]["status_sheet"])

    # Initialize client.
    def initialize_client(self):
        """Initialates smartsheet client and returns smartsheet_client variable."""
        smartsheet_client = smartsheet.Smartsheet(self.smartsheet_access_token)
        smartsheet_client.errors_as_exceptions(True)
        return smartsheet_client

    # Get all webhooks owned by the user.
    def get_webhooks(self):
        """Return a list conatining all webhooks owned by the user."""
        hooks_response = self.smartsheet_client.Webhooks.list_webhooks(include_all=True)
        print(f"[Initialize] - Found {hooks_response.total_count} hooks owned by user")
        return hooks_response

    # Check the sheet can be accessed.
    def probe_sheet(self, target_sheet_id):
        """Checks that sheet with id of target_sheet_id exists."""
        print(f"[Initialize] - Checking for sheet id: {target_sheet_id}")
        # Gets sheet to check sheet exists and can be accessed.
        sheet_response =  self.smartsheet_client.Sheets.get_sheet(target_sheet_id)
        print(f"[Initialize] - Found sheet: {sheet_response.name} at {sheet_response.permalink}")

    # Initialize webhook.
    def initialize_hook(self, target_sheet_id):
        """Finds or creates then initialize and enables webhook."""
        # A webhook only needs to be created once, but hooks get disabled if validation or callbacks fail.
        try:
            webhook = None
            # Interates through webooks to check if webhook already exists.
            for hook in self.webhooks.data:
                if hook.scope_object_id == target_sheet_id and hook.name == self.webhook_name and hook.callback_url == self.call_back_url:
                    webhook = hook
                    print(
                        f"[Initialize] - Found matching hook with id: {webhook.id}")
                    break

            # Webhooks don't exists so attempts to create a new webhook.
            if webhook == None:
                create_response = self.smartsheet_client.Webhooks.create_webhook(
                    smartsheet.models.Webhook({
                        'name': self.webhook_name,
                        'callbackUrl': self.call_back_url,
                        'scope': 'sheet',
                        'scopeObjectId': target_sheet_id,
                        'events': ['*.*'],
                        'version': 1}))
                webhook = create_response.result
                print(f"[Initialize] - Created new hook: {webhook.id}")

            # Checks webhook is enabled and pointing to our current url
            update_response = self.smartsheet_client.Webhooks.update_webhook(
                webhook.id, self.smartsheet_client.models.Webhook({'enabled': True}))
            updated_webhook = update_response.result
            print(
                f"[Initialize] - Hook enabled: {updated_webhook.enabled}, status: {updated_webhook.status}")
        except Exception as e:
            print(e)
