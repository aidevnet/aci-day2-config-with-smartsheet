import smartsheet
import sys
import acitoolkit.acitoolkit as ACI
import configparser

config = configparser.ConfigParser()
config.read("../config.ini")

def main():

    smartsheet_client = smartsheet.Smartsheet(config["Environment"]["smartsheet_API_key"])

    for apic in config['Environment']['APICs'].split(','):

        # Login to APIC
        session = ACI.Session(config[apic]["hostname"], config[apic]["username"], config[apic]["password"])
        resp = session.login()
        if not resp.ok:
            print('%% Could not login to '+ apic)
            sys.exit(0)

        # Download all of the tenants
        tenants = ACI.Tenant.get(session)
        tenants_list=[]
        for tenant in tenants:
            tenants_list.append(tenant.name)
    
        # Specify column properties
        column_spec = smartsheet.models.Column({
            'title': apic,
            'type': 'PICKLIST',
            'options': tenants_list,
            'index': int(config[apic]["tenant_column_id_index"])
        })

        # Update column
        response = smartsheet_client.Sheets.update_column(
            config["ACI Provisioning Start Point"]["sheet_id"],       # sheet_id
            config[apic]["tenant_column_id"],                         # column_id
            column_spec)

        updated_column = response.result
 
if __name__ == '__main__':
    main()
