import smartsheet
import requests
import json
import yaml
import subprocess
import configparser

requests.packages.urllib3.disable_warnings()

config = configparser.ConfigParser()
config.read("config.ini")

class Process:
    def __init__(self, smartsheet_client):
        self.smartsheet_client = smartsheet_client

    # Processes callbackData and retrieves changed values.
    def process_events(self, callbackData, smartsheet_client):
        """Processes callbackData and retrieves and prints new cell values from sheet."""
        if callbackData["scope"] != "sheet":
            return
        # Get Sheet with changes
        sheet_response = self.smartsheet_client.Sheets.get_sheet(callbackData["scopeObjectId"])
        # Interates through changes in callbackData.
        for event in callbackData["events"]:
            if event["objectType"] == "cell":
                row_id = event["rowId"]
                column_id = event["columnId"]
                print(f"[Sheet Update] - Cell changed, row id: {row_id}, column id {column_id}")
                response = self.smartsheet_client.Sheets.get_row(callbackData["scopeObjectId"], row_id)
                dict_response = response.to_dict()
                # Process the data that is input in the ACI Provisioning Start Point smartsheet
                if dict_response['sheetId'] == int(config['ACI Provisioning Start Point']['sheet_id']):
                    cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }
                    use_case = cell_map[int(config["ACI Provisioning Start Point"]["use_case_column_id"])]["value"] 
                    site = cell_map[int(config["ACI Provisioning Start Point"]["site_column_id"])]["value"]

                    if use_case == "Deploy an App":                    
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Deploy an App']['sheet_id'],   # sheet-id
                            config['Deploy an App']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Deploy an App']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]["tenant_column_id"])]["value"]
                            tenant_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['tenant_column_id'],   # column-id
                                {
                                    'title': 'Tenant',
                                    'type': 'PICKLIST',
                                    'options': site_tenant,
                                    'index': int(config['Deploy an App']['tenant_column_index'])
                                }
                            )
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of VRFs for specific Tenant
                            r_vrf = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvCtx', cookies=cookie, verify=False).json()
                            vrf_list=[]
                            for data in r_vrf["imdata"]:
                                vrf_list.append(data["fvCtx"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the VRF information
                            vrf_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['vrf_name_column_id'],   # column-id
                                {
                                    'title': 'VRF Name',
                                    'type': 'PICKLIST',
                                    'options': vrf_list,
                                    'index': int(config['Deploy an App']['vrf_column_index'])
                                }
                            )
                            # Get list of BDs for specific Tenant
                            r_bd = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvBD', cookies=cookie, verify=False).json()
                            bd_list=[]
                            for data in r_bd["imdata"]:
                                bd_list.append(data["fvBD"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the BD information
                            bd_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['bridge_domain_column_id'],   # column-id
                                {
                                    'title': 'Bridge Domain (BD)',
                                    'type': 'PICKLIST',
                                    'options': bd_list,
                                    'index': int(config['Deploy an App']['bd_column_index'])
                                }
                            )
                            # Get list of L3Outs for specific Tenant
                            r_l3out = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=l3extOut', cookies=cookie, verify=False).json()
                            l3out_list=[]
                            for data in r_l3out["imdata"]:
                                l3out_list.append(data["l3extOut"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the L3Out information
                            l3out_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['bd_l3out_column_id'],   # column-id
                                {
                                    'title': 'BD L3Out Name',
                                    'type': 'PICKLIST',
                                    'options': l3out_list,
                                    'index': int(config['Deploy an App']['l3out_column_index'])
                                }
                            )
                            # Get list of applications for specific Tenant
                            r_app = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAp', cookies=cookie, verify=False).json()
                            app_list=[]
                            for data in r_app["imdata"]:
                                app_list.append(data["fvAp"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the application information
                            app_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['app_name_column_id'],   # column-id
                                {
                                    'title': 'Application Name',
                                    'type': 'PICKLIST',
                                    'options': app_list,
                                    'index': int(config['Deploy an App']['app_column_index'])
                                }
                            )
                            # Get list of EPGs for specific Tenant
                            r_epg = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAEPg', cookies=cookie, verify=False).json()
                            epg_list=[]
                            for data in r_epg["imdata"]:
                                epg_list.append(data["fvAEPg"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the EPGs information
                            epg_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['epg_name_column_id'],   # column-id
                                {
                                    'title': 'Endpoint Group (EPG) Name',
                                    'type': 'PICKLIST',
                                    'options': epg_list,
                                    'index': int(config['Deploy an App']['epg_column_index'])
                                }
                            )
                            # Get list of Domains
                            r_domain = requests.get(config[site]['hostname']+'/api/node/class/physDomP.json', cookies=cookie, verify=False).json()
                            domain_list=[]
                            for data in r_domain["imdata"]:
                                domain_list.append(data["physDomP"]["attributes"]["name"])
                            
                            # Update Deploy an App smartsheet drop down with the domain information
                            domain_update = self.smartsheet_client.Sheets.update_column(
                                config['Deploy an App']['sheet_id'],   # sheet-id
                                config['Deploy an App']['domain_name_column_id'],   # column-id
                                {
                                    'title': 'Domain Name',
                                    'type': 'PICKLIST',
                                    'options': domain_list,
                                    'index': int(config['Deploy an App']['domain_column_index'])
                                }
                            )

                    elif use_case == "Create Static Path Binding":                  
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Create Static Path Binding']['sheet_id'],   # sheet-id
                            config['Create Static Path Binding']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Create Static Path Binding']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]['tenant_column_id'])]["value"]
                            tenant_update = self.smartsheet_client.Sheets.update_column(
                                config['Create Static Path Binding']['sheet_id'],   # sheet-id
                                config['Create Static Path Binding']['tenant_column_id'],   # column-id
                                {
                                    'title': 'Tenant',
                                    'type': 'PICKLIST',
                                    'options': site_tenant,
                                    'index': int(config['Create Static Path Binding']['tenant_column_index'])
                                }
                            )
                            # Authenticate to APIC 1
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of applications for specific Tenant
                            r_app = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAp', cookies=cookie, verify=False).json()
                            app_list=[]
                            for data in r_app["imdata"]:
                                app_list.append(data["fvAp"]["attributes"]["name"])
                            
                            # Update Create Static Path Binding smartsheet drop down with the application information
                            app_update = self.smartsheet_client.Sheets.update_column(
                                config['Create Static Path Binding']['sheet_id'],   # sheet-id
                                config['Create Static Path Binding']['app_profile_column_id'],   # column-id
                                {
                                    'title': 'App Profile',
                                    'type': 'PICKLIST',
                                    'options': app_list,
                                    'index': int(config['Create Static Path Binding']['app_column_index'])
                                }
                            )
                            # Get list of EPGs for specific Tenant
                            r_epg = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAEPg', cookies=cookie, verify=False).json()
                            epg_list=[]
                            for data in r_epg["imdata"]:
                                epg_list.append(data["fvAEPg"]["attributes"]["name"])
                            
                            # Update Create Static Path Binding smartsheet drop down with the EPGs information
                            epg_update = self.smartsheet_client.Sheets.update_column(
                                config['Create Static Path Binding']['sheet_id'],   # sheet-id
                                config['Create Static Path Binding']['epg_name_column_id'],   # column-id
                                {
                                    'title': 'Endpoint Group (EPG) Name',
                                    'type': 'PICKLIST',
                                    'options': epg_list,
                                    'index': int(config['Create Static Path Binding']['epg_column_index'])
                                }
                            )                        
                            # Get list of interfaces
                            r_int = requests.get(config[site]['hostname']+'/api/node/class/topology/pod-1/l1PhysIf.json?order-by=l1PhysIf.id', cookies=cookie, verify=False).json()
                            int_list=[]
                            for data in r_int["imdata"]:
                                int_list.append(data["l1PhysIf"]["attributes"]["id"])
                            
                            # Update Create Static Path Binding smartsheet drop down with the interface information
                            int_update = self.smartsheet_client.Sheets.update_column(
                                config['Create Static Path Binding']['sheet_id'],   # sheet-id
                                config['Create Static Path Binding']['interface_column_id'],   # column-id
                                {
                                    'title': 'Interface',
                                    'type': 'PICKLIST',
                                    'options': int_list,
                                    'index': int(config['Create Static Path Binding']['interface_column_index'])
                                }
                            )

                    elif use_case == "Configure Filters":                  
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Configure Filters']['sheet_id'],   # sheet-id
                            config['Configure Filters']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Configure Filters']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]['tenant_column_id'])]["value"]
                            tenant_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Filters']['sheet_id'],   # sheet-id
                                config['Configure Filters']['tenant_column_id'],   # column-id
                                {
                                    'title': 'Tenant',
                                    'type': 'PICKLIST',
                                    'options': site_tenant,
                                    'index': int(config['Configure Filters']['tenant_column_index'])
                                }
                            )
                            # Authenticate to APIC 1
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of filters for specific Tenant
                            r_filter = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=vzFilter', cookies=cookie, verify=False).json()
                            filter_list=[]
                            for data in r_filter["imdata"]:
                                filter_list.append(data["vzFilter"]["attributes"]["name"])
                            
                            # Update Configure Filter smartsheet drop down with the filter information
                            filter_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Filters']['sheet_id'],   # sheet-id
                                config['Configure Filters']['filter_name_column_id'],   # column-id
                                {
                                    'title': 'Filter Name',
                                    'type': 'PICKLIST',
                                    'options': filter_list,
                                    'index': int(config['Configure Filters']['filter_column_index'])
                                }
                            )
                            # Get list of filter descriptions for specific Tenant
                            r_filter_desc = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=vzFilter', cookies=cookie, verify=False).json()
                            filter_desc_list=[]
                            for data in r_filter_desc["imdata"]:
                                filter_desc_list.append(data["vzFilter"]["attributes"]["descr"])
                            
                            # Update Configure Filter smartsheet drop down with the filter description information
                            filter_desc_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Filters']['sheet_id'],   # sheet-id
                                config['Configure Filters']['filter_description_column_id'],   # column-id
                                {
                                    'title': 'Filter Description',
                                    'type': 'PICKLIST',
                                    'options': filter_desc_list,
                                    'index': int(config['Configure Filters']['filter_desc_column_index'])
                                }
                            )
                            # Get filter entries for each filter
                            filter_entry_list=[]                        
                            for filter_entry in filter_list:
                                r_filter_entry = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'/flt-'+filter_entry+'.json?query-target=children&target-subtree-class=vzEntry&query-target-filter=not(wcard(vzEntry.dn,"__ui_"))', cookies=cookie, verify=False).json()
                                for data in r_filter_entry["imdata"]:
                                    filter_entry_list.append(data["vzEntry"]["attributes"]["name"])
                            # Update Configure Filter smartsheet drop down with the filter entry information
                            filter_entry_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Filters']['sheet_id'],   # sheet-id
                                config['Configure Filters']['entry_column_id'],   # column-id
                                {
                                    'title': 'Entry',
                                    'type': 'PICKLIST',
                                    'options': filter_entry_list,
                                    'index': int(config['Configure Filters']['filter_entry_column_index'])
                                }
                            )                       

                    elif use_case == "Configure Contracts":                  
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Configure Contracts']['sheet_id'],   # sheet-id
                            config['Configure Contracts']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Configure Contracts']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]['tenant_column_id'])]["value"]
                            tenant_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Contracts']['sheet_id'],   # sheet-id
                                config['Configure Contracts']['tenant_column_id'],   # column-id
                                {
                                    'title': 'Tenant',
                                    'type': 'PICKLIST',
                                    'options': site_tenant,
                                    'index': int(config['Configure Contracts']['tenant_column_index'])
                                }
                            )
                            # Authenticate to APIC 1
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of contracts for specific Tenant
                            r_contract = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=vzBrCP', cookies=cookie, verify=False).json()
                            contract_list=[]
                            contract_desc_list=[]
                            for data in r_contract["imdata"]:
                                contract_list.append(data["vzBrCP"]["attributes"]["name"])
                                contract_desc_list.append(data["vzBrCP"]["attributes"]["descr"])
                            
                            # Update Configure Contract smartsheet drop down with the contract information
                            contract_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Contracts']['sheet_id'],   # sheet-id
                                config['Configure Contracts']['contract_column_id'],   # column-id
                                {
                                    'title': 'Contract',
                                    'type': 'PICKLIST',
                                    'options': contract_list,
                                    'index': int(config['Configure Contracts']['contract_column_index'])
                                }
                            )
                            # Update Configure Contract smartsheet drop down with the contract description information
                            contract_desc_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Contracts']['sheet_id'],   # sheet-id
                                config['Configure Contracts']['contract_description_column_id'],   # column-id
                                {
                                    'title': 'Contract Description',
                                    'type': 'PICKLIST',
                                    'options': contract_desc_list,
                                    'index': int(config['Configure Contracts']['contract_desc_column_index'])
                                }
                            )
                            # Get list of subjects and filters for specific Tenant
                            subject_list=[]
                            filter_list=[]
                            for contract in contract_list:
                                r_subject_filter = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'/brc-'+contract+'.json?query-target=subtree&target-subtree-class=vzSubj&query-target-filter=not(wcard(vzSubj.dn,"__ui_"))', cookies=cookie, verify=False).json()
                                for data in r_subject_filter["imdata"]:
                                    subject_list.append(data["vzSubj"]["attributes"]["name"])
                                r_filter = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'/brc-'+contract+'.json?query-target=subtree&target-subtree-class=vzRsSubjFiltAtt,vzRsFiltAtt&query-target=subtree', cookies=cookie, verify=False).json()
                                for data in r_filter["imdata"]:
                                    filter_list.append(data["vzRsSubjFiltAtt"]["attributes"]["tnVzFilterName"])
                            
                            # Update Configure Contract smartsheet drop down with the subject information
                            subject_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Contracts']['sheet_id'],   # sheet-id
                                config['Configure Contracts']['subject_column_id'],   # column-id
                                {
                                    'title': 'Subject',
                                    'type': 'PICKLIST',
                                    'options': subject_list,
                                    'index': int(config['Configure Contracts']['subject_column_index'])
                                }
                            )
                            # Update Configure Contract smartsheet drop down with the filter information
                            filter_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Contracts']['sheet_id'],   # sheet-id
                                config['Configure Contracts']['filter_column_id'],   # column-id
                                {
                                    'title': 'Filter',
                                    'type': 'PICKLIST',
                                    'options': filter_list,
                                    'index': int(config['Configure Contracts']['filter_column_index'])
                                }
                            )

                    elif use_case == "Associate EPGs to Contracts":                  
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Associate EPGs to Contracts']['sheet_id'],   # sheet-id
                            config['Associate EPGs to Contracts']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Associate EPGs to Contracts']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]['tenant_column_id'])]["value"]
                            tenant_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate EPGs to Contracts']['sheet_id'],   # sheet-id
                                config['Associate EPGs to Contracts']['tenant_column_id'],   # column-id
                                {
                                    'title': 'Tenant',
                                    'type': 'PICKLIST',
                                    'options': site_tenant,
                                    'index': int(config['Associate EPGs to Contracts']['tenant_column_index'])
                                }
                            )
                            # Authenticate to APIC 1
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of contracts for specific Tenant
                            r_contract = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=vzBrCP', cookies=cookie, verify=False).json()
                            contract_list=[]
                            for data in r_contract["imdata"]:
                                contract_list.append(data["vzBrCP"]["attributes"]["name"])
                            
                            # Update Associate EPGs to Contracts smartsheet drop down with the contract information
                            contract_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate EPGs to Contracts']['sheet_id'],   # sheet-id
                                config['Associate EPGs to Contracts']['contract_column_id'],   # column-id
                                {
                                    'title': 'Contract',
                                    'type': 'PICKLIST',
                                    'options': contract_list,
                                    'index': int(config['Associate EPGs to Contracts']['contract_column_index'])
                                }
                            )
                            # Get list of applications for specific Tenant
                            r_app = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAp', cookies=cookie, verify=False).json()
                            app_list=[]
                            for data in r_app["imdata"]:
                                app_list.append(data["fvAp"]["attributes"]["name"])
                            
                            # Update Create Static Path Binding smartsheet drop down with the application information
                            app_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate EPGs to Contracts']['sheet_id'],   # sheet-id
                                config['Associate EPGs to Contracts']['app_column_id'],   # column-id
                                {
                                    'title': 'App',
                                    'type': 'PICKLIST',
                                    'options': app_list,
                                    'index': int(config['Associate EPGs to Contracts']['app_column_index'])
                                }
                            )
                            # Get list of EPGs for specific Tenant
                            r_epg = requests.get(config[site]['hostname']+'/api/node/mo/uni/tn-'+site_tenant+'.json?query-target=subtree&target-subtree-class=fvAEPg', cookies=cookie, verify=False).json()
                            epg_list=[]
                            for data in r_epg["imdata"]:
                                epg_list.append(data["fvAEPg"]["attributes"]["name"])
                            
                            # Update Create Static Path Binding smartsheet drop down with the EPGs information
                            epg_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate EPGs to Contracts']['sheet_id'],   # sheet-id
                                config['Associate EPGs to Contracts']['epg_column_id'],   # column-id
                                {
                                    'title': 'EPG',
                                    'type': 'PICKLIST',
                                    'options': epg_list,
                                    'index': int(config['Associate EPGs to Contracts']['epg_column_index'])
                                }
                            )

                    elif use_case == "Configure Policy Groups":                  
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Configure Policy Groups']['sheet_id'],   # sheet-id
                            config['Configure Policy Groups']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Configure Policy Groups']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            site_tenant = cell_map[int(config[site]['tenant_column_id'])]["value"]

                            # Authenticate to APIC 1
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of AEPs
                            r_aep = requests.get(config[site]['hostname']+'/api/node/class/infraAttEntityP.json', cookies=cookie, verify=False).json()
                            aep_list=[]
                            for data in r_aep["imdata"]:
                                aep_list.append(data["infraAttEntityP"]["attributes"]["name"])
                            
                            # Update Configure Policy Groups smartsheet drop down with the aep information
                            aep_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['aep_column_id'],   # column-id
                                {
                                    'title': 'AEP',
                                    'type': 'PICKLIST',
                                    'options': aep_list,
                                    'index': int(config['Configure Policy Groups']['aep_column_index'])
                                }
                            )
                            # Get list of CDP Policies
                            r_cdp = requests.get(config[site]['hostname']+'/api/node/class/cdpIfPol.json', cookies=cookie, verify=False).json()
                            cdp_list=[]
                            for data in r_cdp["imdata"]:
                                cdp_list.append(data["cdpIfPol"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the CDP policies information
                            cdp_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['cdp_policy_column_id'],   # column-id
                                {
                                    'title': 'CDP Policy',
                                    'type': 'PICKLIST',
                                    'options': cdp_list,
                                    'index': int(config['Configure Policy Groups']['cdp_column_index'])
                                }
                            )
                            # Get list of PortChannel policies
                            r_portchannel = requests.get(config[site]['hostname']+'/api/node/class/lacpIfPol.json', cookies=cookie, verify=False).json()
                            portchannel_list=[]
                            for data in r_portchannel["imdata"]:
                                portchannel_list.append(data["lacpIfPol"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the portchannel policy information
                            portchannel_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['portchannel_policy_column_id'],   # column-id
                                {
                                    'title': 'PortChannel Policy',
                                    'type': 'PICKLIST',
                                    'options': portchannel_list,
                                    'index': int(config['Configure Policy Groups']['portchannel_column_index'])
                                }
                            )
                            # Get list of LinkLevel policies
                            r_linklevel = requests.get(config[site]['hostname']+'/api/node/class/fabricHIfPol.json', cookies=cookie, verify=False).json()
                            linklevel_list=[]
                            for data in r_linklevel["imdata"]:
                                linklevel_list.append(data["fabricHIfPol"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the linklevel policy information
                            linklevel_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['link_level_policy_column_id'],   # column-id
                                {
                                    'title': 'Link-Level Policy',
                                    'type': 'PICKLIST',
                                    'options': linklevel_list,
                                    'index': int(config['Configure Policy Groups']['linklevel_column_index'])
                                }
                            )
                            # Get list of MCP policies
                            r_mcp = requests.get(config[site]['hostname']+'/api/node/class/mcpIfPol.json', cookies=cookie, verify=False).json()
                            mcp_list=[]
                            for data in r_mcp["imdata"]:
                                linklevel_list.append(data["mcpIfPol"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the mcp policy information
                            mcp_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['mcp_policy_column_id'],   # column-id
                                {
                                    'title': 'MCP Policy',
                                    'type': 'PICKLIST',
                                    'options': mcp_list,
                                    'index': int(config['Configure Policy Groups']['mcp_column_index'])
                                }
                            )
                            # Get list of Policy Group Names
                            r_policy_group = requests.get(config[site]['hostname']+'/api/node/class/infraAccGrp.json', cookies=cookie, verify=False).json()
                            policy_group_list=[]
                            for data in r_policy_group["imdata"]:
                                policy_group_list.append(data["infraAccGrp"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the policy group information
                            policy_group_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['policy_group_name_column_id'],   # column-id
                                {
                                    'title': 'Policy Group Name',
                                    'type': 'PICKLIST',
                                    'options': policy_group_list,
                                    'index': int(config['Configure Policy Groups']['policy_group_column_index'])
                                }
                            )
                            # Get list of LLDP policies
                            r_lldp = requests.get(config[site]['hostname']+'/api/node/class/lldpIfPol.json', cookies=cookie, verify=False).json()
                            lldp_list=[]
                            for data in r_lldp["imdata"]:
                                lldp_list.append(data["lldpIfPol"]["attributes"]["name"])
                            
                            # Update Configure Policy Group smartsheet drop down with the policy group information
                            lldp_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Policy Groups']['sheet_id'],   # sheet-id
                                config['Configure Policy Groups']['lldp_policy_column_id'],   # column-id
                                {
                                    'title': 'LLDP Policy',
                                    'type': 'PICKLIST',
                                    'options': lldp_list,
                                    'index': int(config['Configure Policy Groups']['lldp_column_index'])
                                }
                            )

                    elif use_case == "Configure Switch & Interface Profiles":
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Configure Switch & Interface Profiles']['sheet_id'],   # sheet-id
                            config['Configure Switch & Interface Profiles']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Configure Switch & Interface Profiles']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            # Authenticate to APIC
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get list of leaf IDs
                            r_leaf = requests.get(config[site]['hostname']+'/api/node/class/topology/pod-1/topSystem.json?query-target-filter=eq(topSystem.role,"leaf")', cookies=cookie, verify=False).json()
                            leaf_list=[]
                            for data in r_leaf["imdata"]:
                                leaf_list.append(data["topSystem"]["attributes"]["id"])
                            
                            # Update Configure Switch & Interface Profiles smartsheet drop down with the leaf ID information
                            leaf_update = self.smartsheet_client.Sheets.update_column(
                                config['Configure Switch & Interface Profiles']['sheet_id'],   # sheet-id
                                config['Configure Switch & Interface Profiles']['leaf_id_columm_id'],   # column-id
                                {
                                    'title': 'Leaf ID',
                                    'type': 'PICKLIST',
                                    'options': leaf_list,
                                    'index': int(config['Configure Switch & Interface Profiles']['leaf_column_index'])
                                }
                            )

                    elif use_case == "Associate Int to Policy Groups":
                        site_update = self.smartsheet_client.Sheets.update_column(
                            config['Associate Int to Policy Groups']['sheet_id'],   # sheet-id
                            config['Associate Int to Policy Groups']['site_column_id'],   # column-id
                            {
                                'title': 'Site',
                                'type': 'PICKLIST',
                                'options': site,
                                'index': int(config['Associate Int to Policy Groups']['site_column_index'])
                            }
                        )
                        if site in config['Environment']['APICs'].split(','):
                            # Authenticate to APIC
                            r = requests.post(config[site]['hostname']+'/api/aaaLogin.json', json={"aaaUser":{"attributes":{"name":config[site]['username'],"pwd":config[site]['password']}}}, verify=False)
                            r_json = r.json()
                            token = r_json["imdata"][0]["aaaLogin"]["attributes"]["token"]
                            cookie = {'APIC-cookie':token}

                            # Get interface profiles
                            r_int_profile = requests.get(config[site]['hostname']+'/api/node/class/infraAccPortP.json', cookies=cookie, verify=False).json()
                            int_profile_list=[]
                            for data in r_int_profile["imdata"]:
                                int_profile_list.append(data["infraAccPortP"]["attributes"]["name"])
                            
                            # Update Associate Int to Policy Groups smartsheet drop down with the interface profile information
                            int_profile_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate Int to Policy Groups']['sheet_id'],   # sheet-id
                                config['Associate Int to Policy Groups']['interface_profile_column_id'],   # column-id
                                {
                                    'title': 'Interface Profile',
                                    'type': 'PICKLIST',
                                    'options': int_profile_list,
                                    'index': int(config['Associate Int to Policy Groups']['int_profile_column_index'])
                                }
                            )
                            # Get policy group name
                            r_policy_group = requests.get(config[site]['hostname']+'/api/node/class/infraAccGrp.json', cookies=cookie, verify=False).json()
                            policy_group_list=[]
                            for data in r_policy_group["imdata"]:
                                policy_group_list.append(data["infraAccGrp"]["attributes"]["name"])
                            
                            # Update Associate Int to Policy Groups smartsheet drop down with the policy group name information
                            policy_group_update = self.smartsheet_client.Sheets.update_column(
                                config['Associate Int to Policy Groups']['sheet_id'],   # sheet-id
                                config['Associate Int to Policy Groups']['policy_group_name_column_id'],   # column-id
                                {
                                    'title': 'Policy Group Name',
                                    'type': 'PICKLIST',
                                    'options': policy_group_list,
                                    'index': int(config['Associate Int to Policy Groups']['policy_group_column_index'])
                                }
                            )

                # Deploy an App smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Deploy an App']['sheet_id']):
                    deploy_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            deploy_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Deploy an App']['ready_to_deploy_column_id']) in deploy_cell_map:
                        apic_controller = deploy_cell_map[int(config['Deploy an App']['site_column_id'])]["value"]
                        deploy_tenant = deploy_cell_map[int(config['Deploy an App']['tenant_column_id'])]["value"]
                        deploy_vrf_name = deploy_cell_map[int(config['Deploy an App']['vrf_name_column_id'])]["value"]
                        deploy_bd_name = deploy_cell_map[int(config['Deploy an App']['bridge_domain_column_id'])]["value"]
                        deploy_bd_description = deploy_cell_map[int(config['Deploy an App']['bd_description_column_id'])]["value"]
                        deploy_bd_routing = deploy_cell_map[int(config['Deploy an App']['bd_routing_column_id'])]["value"]
                        deploy_bd_gateway = deploy_cell_map[int(config['Deploy an App']['bd_gateway_column_id'])]["value"]
                        deploy_bd_mask = int(deploy_cell_map[int(config['Deploy an App']['bd_mask_column_id'])]["value"])
                        deploy_bd_scope = deploy_cell_map[int(config['Deploy an App']['bd_scope_column_id'])]["value"]
                        deploy_l3_out = deploy_cell_map[int(config['Deploy an App']['bd_l3out_column_id'])]["value"]
                        deploy_app_name = deploy_cell_map[int(config['Deploy an App']['app_name_column_id'])]["value"]
                        deploy_epg_name = deploy_cell_map[int(config['Deploy an App']['epg_name_column_id'])]["value"]
                        deploy_epg_description = deploy_cell_map[int(config['Deploy an App']['epg_description_column_id'])]["value"]
                        deploy_epg_priority = deploy_cell_map[int(config['Deploy an App']['epg_priority_column_id'])]["value"]
                        deploy_domain_name = deploy_cell_map[int(config['Deploy an App']['domain_name_column_id'])]["value"]
                        deploy_domain_type = deploy_cell_map[int(config['Deploy an App']['domain_type_column_id'])]["value"]
                        deploy_req_id = deploy_cell_map[int(config['Deploy an App']['request_id_column_id'])]["value"]
                        deploy_entry_date = deploy_cell_map[int(config['Deploy an App']['date_of_entry_column_id'])]["value"]
                        deploy_user_email = deploy_cell_map[int(config['Deploy an App']['entered_by_column_id'])]["value"]
                        deploy_provision_date = deploy_cell_map[int(config['Deploy an App']['date_of_provisioning_column_id'])]["value"]

                        app_var_fname = "Deploy-App/app-var.yml"
                        var_stream = open(app_var_fname, 'r')
                        app_var_data = yaml.load(var_stream, Loader=yaml.FullLoader)

                        app_var_data['tenants'][0]['tenant'] = deploy_tenant
                        app_var_data['tenants'][0]['tenant_description'] = deploy_tenant + " - Tenant created using Ansible and Python"
                        app_var_data['vrfs'][0]['tenant'] = deploy_tenant
                        app_var_data['vrfs'][0]['vrf'] = deploy_vrf_name
                        app_var_data['vrfs'][0]['vrf_description'] = deploy_vrf_name + " - VRF created using Ansible and Python"
                        app_var_data['bds'][0]['tenant'] = deploy_tenant
                        app_var_data['bds'][0]['vrf'] = deploy_vrf_name
                        app_var_data['bds'][0]['bd'] = deploy_bd_name
                        app_var_data['bds'][0]['bd_description'] = deploy_bd_description
                        app_var_data['bds'][0]['bd_routing'] = deploy_bd_routing
                        app_var_data['bd_subnets'][0]['tenant'] = deploy_tenant
                        app_var_data['bd_subnets'][0]['bd'] = deploy_bd_name
                        app_var_data['bd_subnets'][0]['bd_gateway'] = deploy_bd_gateway
                        app_var_data['bd_subnets'][0]['bd_mask'] = deploy_bd_mask
                        app_var_data['bd_subnets'][0]['bd_scope'] = deploy_bd_scope
                        app_var_data['bd_l3out'][0]['tenant'] = deploy_tenant
                        app_var_data['bd_l3out'][0]['bd'] = deploy_bd_name
                        app_var_data['bd_l3out'][0]['bd_l3out'] = deploy_l3_out
                        app_var_data['apps'][0]['tenant'] = deploy_tenant
                        app_var_data['apps'][0]['app'] = deploy_app_name
                        app_var_data['apps'][0]['app_description'] = deploy_app_name + " - App Profile created using Ansible and Python"
                        app_var_data['epgs'][0]['tenant'] = deploy_tenant
                        app_var_data['epgs'][0]['app'] = deploy_app_name
                        app_var_data['epgs'][0]['epg'] = deploy_epg_name
                        app_var_data['epgs'][0]['epg_description'] = deploy_epg_description
                        app_var_data['epgs'][0]['bd'] = deploy_bd_name
                        app_var_data['epgs'][0]['epg_priority'] = deploy_epg_priority
                        app_var_data['domains'][0]['domain'] = deploy_domain_name
                        app_var_data['domains'][0]['domain_type'] = deploy_domain_type
                        app_var_data['epg_to_domain'][0]['tenant'] = deploy_tenant
                        app_var_data['epg_to_domain'][0]['app'] = deploy_app_name
                        app_var_data['epg_to_domain'][0]['epg'] = deploy_epg_name
                        app_var_data['epg_to_domain'][0]['domain'] = deploy_domain_name
                        app_var_data['epg_to_domain'][0]['domain_type'] = deploy_domain_type

                        temp_app_var_fname = "Deploy-App/app-var-"+deploy_req_id+".yml"

                        with open(temp_app_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(app_var_data, default_flow_style=False, sort_keys=False))

                        deploy_app_fname = "Deploy-App/deploy-app.yml"
                        deploy_stream = open(deploy_app_fname, 'r')
                        deploy_app_data = yaml.load(deploy_stream, Loader=yaml.FullLoader)

                        deploy_app_data[0]['hosts'] = apic_controller
                        deploy_app_data[0]['tasks'][0]['include_vars']['file'] = temp_app_var_fname.split("/")[1]

                        temp_deploy_app_fname = "Deploy-App/deploy-app-"+deploy_req_id+".yml"

                        with open(temp_deploy_app_fname, 'w') as deploy_yaml_file:
                            deploy_yaml_file.write(yaml.dump(deploy_app_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Deploy-App/inventory.yml", "{}".format(temp_deploy_app_fname)]
                        ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = ansible_output.communicate()

                        ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Deploy an App']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Deploy an App']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Deploy an App']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Configure Filters smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Configure Filters']['sheet_id']):
                    filters_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            filters_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Configure Filters']['ready_to_deploy_column_id']) in filters_cell_map:
                        apic_controller = filters_cell_map[int(config['Configure Filters']['site_column_id'])]["value"]
                        filters_tenant = filters_cell_map[int(config['Configure Filters']['tenant_column_id'])]["value"]
                        filters_name = filters_cell_map[int(config['Configure Filters']['filter_name_column_id'])]["value"]
                        filters_description = filters_cell_map[int(config['Configure Filters']['filter_description_column_id'])]["value"]
                        filters_entry = filters_cell_map[int(config['Configure Filters']['entry_column_id'])]["value"]
                        filters_ethertype = filters_cell_map[int(config['Configure Filters']['ethertype_column_id'])]["value"]
                        filters_ip_proto = filters_cell_map[int(config['Configure Filters']['ip_protocol_column_id'])]["value"]
                        filters_port_start = int(filters_cell_map[int(config['Configure Filters']['port_start_column_id'])]["value"])
                        filters_port_end = int(filters_cell_map[int(config['Configure Filters']['port_end_column_id'])]["value"])
                        filters_req_id = filters_cell_map[int(config['Configure Filters']['request_id_column_id'])]["value"]
                        filters_entry_date = filters_cell_map[int(config['Configure Filters']['date_of_entry_column_id'])]["value"]
                        filters_user_email = filters_cell_map[int(config['Configure Filters']['entered_by_column_id'])]["value"]
                        filters_provision_date = filters_cell_map[int(config['Configure Filters']['date_of_provisioning_column_id'])]["value"]

                        filter_var_fname = "Configure-Filters/filters-var.yml"
                        filter_var_stream = open(filter_var_fname, 'r')
                        filter_var_data = yaml.load(filter_var_stream, Loader=yaml.FullLoader)

                        filter_var_data['filters'][0]['tenant'] = filters_tenant
                        filter_var_data['filters'][0]['filter'] = filters_name
                        filter_var_data['filters'][0]['filter_description'] = filters_description + " - Filter created using Ansible and Python"
                        filter_var_data['filter_entries'][0]['tenant'] = filters_tenant
                        filter_var_data['filter_entries'][0]['filter'] = filters_name
                        filter_var_data['filter_entries'][0]['entry'] = filters_entry
                        filter_var_data['filter_entries'][0]['ether_type'] = filters_ethertype
                        filter_var_data['filter_entries'][0]['ip_protocol'] = filters_ip_proto
                        filter_var_data['filter_entries'][0]['port_start'] = filters_port_start
                        filter_var_data['filter_entries'][0]['port_end'] = filters_port_end

                        temp_filter_var_fname = "Configure-Filters/filters-var-"+filters_req_id+".yml"

                        with open(temp_filter_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(filter_var_data, default_flow_style=False, sort_keys=False))

                        filters_playbook_fname = "Configure-Filters/filters-playbook.yml"
                        filters_stream = open(filters_playbook_fname, 'r')
                        filters_playbook_data = yaml.load(filters_stream, Loader=yaml.FullLoader)

                        filters_playbook_data[0]['hosts'] = apic_controller
                        filters_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_filter_var_fname.split("/")[1]

                        temp_filters_playbook_fname = "Configure-Filters/filters-playbook-"+filters_req_id+".yml"

                        with open(temp_filters_playbook_fname, 'w') as filters_yaml_file:
                            filters_yaml_file.write(yaml.dump(filters_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Configure-Filters/inventory.yml", "{}".format(temp_filters_playbook_fname)]
                        filters_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = filters_ansible_output.communicate()

                        filters_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if filters_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Filters']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif filters_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Filters']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif filters_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Filters']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Configure Contracts smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Configure Contracts']['sheet_id']):
                    contracts_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            contracts_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Configure Contracts']['ready_to_deploy_column_id']) in contracts_cell_map:
                        apic_controller = contracts_cell_map[int(config['Configure Contracts']['site_column_id'])]["value"]
                        contracts_tenant = contracts_cell_map[int(config['Configure Contracts']['tenant_column_id'])]["value"]
                        contracts_name = contracts_cell_map[int(config['Configure Contracts']['contract_column_id'])]["value"]
                        contracts_description = contracts_cell_map[int(config['Configure Contracts']['contract_description_column_id'])]["value"]
                        contracts_scope = contracts_cell_map[int(config['Configure Contracts']['contract_scope_column_id'])]["value"]
                        contracts_subject = contracts_cell_map[int(config['Configure Contracts']['subject_column_id'])]["value"]
                        contracts_subject_desc = contracts_cell_map[int(config['Configure Contracts']['subject_description_column_id'])]["value"]
                        contracts_filter = contracts_cell_map[int(config['Configure Contracts']['filter_column_id'])]["value"]
                        contracts_req_id = contracts_cell_map[int(config['Configure Contracts']['request_id_column_id'])]["value"]
                        contracts_entry_date = contracts_cell_map[int(config['Configure Contracts']['date_of_entry_column_id'])]["value"]
                        contracts_user_email = contracts_cell_map[int(config['Configure Contracts']['entered_by_column_id'])]["value"]
                        contracts_provision_date = contracts_cell_map[int(config['Configure Contracts']['date_of_provisioning_column_id'])]["value"]

                        contract_var_fname = "Configure-Contracts/contracts-subjects-var.yml"
                        contract_var_stream = open(contract_var_fname, 'r')
                        contract_var_data = yaml.load(contract_var_stream, Loader=yaml.FullLoader)

                        contract_var_data['contracts'][0]['tenant'] = contracts_tenant
                        contract_var_data['contracts'][0]['contract'] = contracts_name
                        contract_var_data['contracts'][0]['contract_description'] = contracts_description + " - Contract created using Ansible and Python"
                        contract_var_data['contracts'][0]['contract_scope'] = contracts_scope
                        contract_var_data['contract_subjects'][0]['tenant'] = contracts_tenant
                        contract_var_data['contract_subjects'][0]['contract'] = contracts_name
                        contract_var_data['contract_subjects'][0]['subject'] = contracts_subject
                        contract_var_data['contract_subjects'][0]['subject_description'] = contracts_subject_desc + " - Subject created using Ansible and Python"
                        contract_var_data['contracts_to_filters'][0]['tenant'] = contracts_tenant
                        contract_var_data['contracts_to_filters'][0]['contract'] = contracts_name
                        contract_var_data['contracts_to_filters'][0]['subject'] = contracts_subject
                        contract_var_data['contracts_to_filters'][0]['filter'] = contracts_filter

                        temp_contract_var_fname = "Configure-Contracts/contracts-subjects-var-"+contracts_req_id+".yml"

                        with open(temp_contract_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(contract_var_data, default_flow_style=False, sort_keys=False))

                        contracts_playbook_fname = "Configure-Contracts/contracts-subjects-playbook.yml"
                        contracts_stream = open(contracts_playbook_fname, 'r')
                        contracts_playbook_data = yaml.load(contracts_stream, Loader=yaml.FullLoader)

                        contracts_playbook_data[0]['hosts'] = apic_controller
                        contracts_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_contract_var_fname.split("/")[1]

                        temp_contracts_playbook_fname = "Configure-Contracts/contracts-subjects-playbook-"+contracts_req_id+".yml"

                        with open(temp_contracts_playbook_fname, 'w') as contracts_yaml_file:
                            contracts_yaml_file.write(yaml.dump(contracts_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Configure-Contracts/inventory.yml", "{}".format(temp_contracts_playbook_fname)]
                        contracts_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = contracts_ansible_output.communicate()

                        contracts_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if contracts_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif contracts_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif contracts_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Associate EPGs to Contracts smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Associate EPGs to Contracts']['sheet_id']):
                    epg2c_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            epg2c_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Associate EPGs to Contracts']['ready_to_deploy_column_id']) in epg2c_cell_map:
                        apic_controller = epg2c_cell_map[int(config['Associate EPGs to Contracts']['site_column_id'])]["value"]
                        epg2c_tenant = epg2c_cell_map[int(config['Associate EPGs to Contracts']['tenant_column_id'])]["value"]
                        epg2c_type = epg2c_cell_map[int(config['Associate EPGs to Contracts']['contract_type_column_id'])]["value"]
                        epg2c_epg = epg2c_cell_map[int(config['Associate EPGs to Contracts']['epg_column_id'])]["value"]
                        epg2c_app = epg2c_cell_map[int(config['Associate EPGs to Contracts']['app_column_id'])]["value"]
                        epg2c_contract = epg2c_cell_map[int(config['Associate EPGs to Contracts']['contract_column_id'])]["value"]
                        epg2c_req_id = epg2c_cell_map[int(config['Associate EPGs to Contracts']['request_id_column_id'])]["value"]
                        epg2c_entry_date = epg2c_cell_map[int(config['Associate EPGs to Contracts']['date_of_entry_column_id'])]["value"]
                        epg2c_user_email = epg2c_cell_map[int(config['Associate EPGs to Contracts']['entered_by_column_id'])]["value"]
                        epg2c_provision_date = epg2c_cell_map[int(config['Associate EPGs to Contracts']['date_of_provisioning_column_id'])]["value"]

                        epg2c_var_fname = "Associate-EPGs-Contracts/epg-contract-var.yml"
                        epg2c_var_stream = open(epg2c_var_fname, 'r')
                        epg2c_var_data = yaml.load(epg2c_var_stream, Loader=yaml.FullLoader)

                        epg2c_var_data['epg_to_contracts'][0]['tenant'] = epg2c_tenant
                        epg2c_var_data['epg_to_contracts'][0]['app'] = epg2c_app
                        epg2c_var_data['epg_to_contracts'][0]['epg'] = epg2c_epg
                        epg2c_var_data['epg_to_contracts'][0]['contract'] = epg2c_contract
                        epg2c_var_data['epg_to_contracts'][0]['contract_type'] = epg2c_type

                        temp_epg2c_var_fname = "Associate-EPGs-Contracts/epg-contract-var-"+epg2c_req_id+".yml"

                        with open(temp_epg2c_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(epg2c_var_data, default_flow_style=False, sort_keys=False))

                        epg2c_playbook_fname = "Associate-EPGs-Contracts/epg-contract-playbook.yml"
                        epg2cs_stream = open(epg2c_playbook_fname, 'r')
                        epg2c_playbook_data = yaml.load(epg2cs_stream, Loader=yaml.FullLoader)

                        epg2c_playbook_data[0]['hosts'] = apic_controller
                        epg2c_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_epg2c_var_fname.split("/")[1]

                        temp_epg2c_playbook_fname = "Associate-EPGs-Contracts/epg-contract-playbook-"+epg2c_req_id+".yml"

                        with open(temp_epg2c_playbook_fname, 'w') as epg2c_yaml_file:
                            epg2c_yaml_file.write(yaml.dump(epg2c_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Associate-EPGs-Contracts/inventory.yml", "{}".format(temp_epg2c_playbook_fname)]
                        epg2c_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = epg2c_ansible_output.communicate()

                        epg2c_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if epg2c_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate EPGs to Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif epg2c_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate EPGs to Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif epg2c_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate EPGs to Contracts']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Configure Switch and Interface Profiles smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Configure Switch & Interface Profiles']['sheet_id']):
                    swint_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            swint_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Configure Switch & Interface Profiles']['ready_to_deploy_column_id']) in swint_cell_map:
                        apic_controller = swint_cell_map[int(config['Configure Switch & Interface Profiles']['site_column_id'])]["value"]
                        swint_leaf_id = int(swint_cell_map[int(config['Configure Switch & Interface Profiles']['leaf_id_columm_id'])]["value"])
                        swint_sw_prof = swint_cell_map[int(config['Configure Switch & Interface Profiles']['switch_profile_column_id'])]["value"]
                        swint_sw_prof_desc = swint_cell_map[int(config['Configure Switch & Interface Profiles']['switch_profile_description_column_id'])]["value"]
                        swint_int_prof = swint_cell_map[int(config['Configure Switch & Interface Profiles']['interface_profile_column_id'])]["value"]
                        swint_int_prof_desc = swint_cell_map[int(config['Configure Switch & Interface Profiles']['interface_profile_description_column_id'])]["value"]
                        swint_req_id = swint_cell_map[int(config['Configure Switch & Interface Profiles']['request_id_column_id'])]["value"]
                        swint_entry_date = swint_cell_map[int(config['Configure Switch & Interface Profiles']['date_of_entry_column_id'])]["value"]
                        swint_user_email = swint_cell_map[int(config['Configure Switch & Interface Profiles']['entered_by_column_id'])]["value"]
                        swint_provision_date = swint_cell_map[int(config['Configure Switch & Interface Profiles']['date_of_provisioning_column_id'])]["value"]

                        swint_var_fname = "Configure-Switch-Int-Profiles/switch-to-interface-profile-var.yml"
                        swint_var_stream = open(swint_var_fname, 'r')
                        swint_var_data = yaml.load(swint_var_stream, Loader=yaml.FullLoader)

                        swint_var_data['leaf_profile'][0]['leaf_profile'] = swint_sw_prof
                        swint_var_data['leaf_profile'][0]['leaf_profile_description'] = swint_sw_prof_desc
                        swint_var_data['interface_profile'][0]['leaf_interface_profile'] = swint_int_prof
                        swint_var_data['interface_profile'][0]['leaf_interface_profile_description'] = swint_int_prof_desc
                        swint_var_data['leaf_to_interface_profile'][0]['leaf_profile'] = swint_sw_prof
                        swint_var_data['leaf_to_interface_profile'][0]['leaf_interface_profile'] = swint_int_prof
                        swint_var_data['leaf_node_selector'][0]['leaf_profile'] = swint_sw_prof
                        swint_var_data['leaf_node_selector'][0]['leaf_ID'] = swint_leaf_id

                        temp_swint_var_fname = "Configure-Switch-Int-Profiles/switch-to-interface-profile-var-"+swint_req_id+".yml"

                        with open(temp_swint_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(swint_var_data, default_flow_style=False, sort_keys=False))

                        swint_playbook_fname = "Configure-Switch-Int-Profiles/switch-to-interface-profile-playbook.yml"
                        swints_stream = open(swint_playbook_fname, 'r')
                        swint_playbook_data = yaml.load(swints_stream, Loader=yaml.FullLoader)

                        swint_playbook_data[0]['hosts'] = apic_controller
                        swint_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_swint_var_fname.split("/")[1]

                        temp_swint_playbook_fname = "Configure-Switch-Int-Profiles/switch-to-interface-profile-playbook-"+swint_req_id+".yml"

                        with open(temp_swint_playbook_fname, 'w') as swint_yaml_file:
                            swint_yaml_file.write(yaml.dump(swint_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Configure-Switch-Int-Profiles/inventory.yml", "{}".format(temp_swint_playbook_fname)]
                        swint_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = swint_ansible_output.communicate()

                        swint_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if swint_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Switch & Interface Profiles']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif swint_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Switch & Interface Profiles']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif swint_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Switch & Interface Profiles']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Configure Policy Groups smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Configure Policy Groups']['sheet_id']):
                    pg_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            pg_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Configure Policy Groups']['ready_to_deploy_column_id']) in pg_cell_map:
                        apic_controller = pg_cell_map[int(config['Configure Policy Groups']['site_column_id'])]["value"]
                        pg_aep = pg_cell_map[int(config['Configure Policy Groups']['aep_column_id'])]["value"]
                        pg_desc = pg_cell_map[int(config['Configure Policy Groups']['policy_group_description_column_id'])]["value"]
                        pg_lag = pg_cell_map[int(config['Configure Policy Groups']['lag_type_column_id'])]["value"]
                        pg_cdp = pg_cell_map[int(config['Configure Policy Groups']['cdp_policy_column_id'])]["value"]
                        pg_portchannel = pg_cell_map[int(config['Configure Policy Groups']['portchannel_policy_column_id'])]["value"]
                        pg_link_level = pg_cell_map[int(config['Configure Policy Groups']['link_level_policy_column_id'])]["value"]
                        pg_mcp = pg_cell_map[int(config['Configure Policy Groups']['mcp_policy_column_id'])]["value"]
                        pg_name = pg_cell_map[int(config['Configure Policy Groups']['policy_group_name_column_id'])]["value"]
                        pg_lldp = pg_cell_map[int(config['Configure Policy Groups']['lldp_policy_column_id'])]["value"]
                        pg_req_id = pg_cell_map[int(config['Configure Policy Groups']['request_id_column_id'])]["value"]
                        pg_entry_date = pg_cell_map[int(config['Configure Policy Groups']['date_of_entry_column_id'])]["value"]
                        pg_user_email = pg_cell_map[int(config['Configure Policy Groups']['entered_by_column_id'])]["value"]
                        pg_provision_date = pg_cell_map[int(config['Configure Policy Groups']['date_of_provisioning_column_id'])]["value"]

                        pg_var_fname = "Configure-Policy/policy-group-var.yml"
                        pg_var_stream = open(pg_var_fname, 'r')
                        pg_var_data = yaml.load(pg_var_stream, Loader=yaml.FullLoader)

                        pg_var_data['policy_groups'][0]['lag_type'] = pg_lag
                        pg_var_data['policy_groups'][0]['policy_group_name'] = pg_name
                        pg_var_data['policy_groups'][0]['policy_group_description'] = pg_desc + " - Interface Policy Group created using Ansible and Python"
                        pg_var_data['policy_groups'][0]['aep'] = pg_aep
                        pg_var_data['policy_groups'][0]['cdp_policy'] = pg_cdp
                        pg_var_data['policy_groups'][0]['lldp_policy'] = pg_lldp
                        pg_var_data['policy_groups'][0]['link_level_policy'] = pg_link_level
                        pg_var_data['policy_groups'][0]['mcp_policy'] = pg_mcp

                        temp_pg_var_fname = "Configure-Policy/policy-group-var-"+pg_req_id+".yml"

                        with open(temp_pg_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(pg_var_data, default_flow_style=False, sort_keys=False))

                        pg_playbook_fname = "Configure-Policy/policy-group-playbook.yml"
                        pgs_stream = open(pg_playbook_fname, 'r')
                        pg_playbook_data = yaml.load(pgs_stream, Loader=yaml.FullLoader)

                        pg_playbook_data[0]['hosts'] = apic_controller
                        pg_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_pg_var_fname.split("/")[1]

                        temp_pg_playbook_fname = "Configure-Policy/policy-group-playbook-"+pg_req_id+".yml"

                        with open(temp_pg_playbook_fname, 'w') as pg_yaml_file:
                            pg_yaml_file.write(yaml.dump(pg_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Configure-Policy/inventory.yml", "{}".format(temp_pg_playbook_fname)]
                        pg_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = pg_ansible_output.communicate()

                        pg_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if pg_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif pg_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif pg_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Configure Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Configure Int to Policy Group smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Associate Int to Policy Groups']['sheet_id']):
                    intpo_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            intpo_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }

                    if int(config['Associate Int to Policy Groups']['ready_to_deploy_column_id']) in intpo_cell_map:
                        apic_controller = intpo_cell_map[int(config['Associate Int to Policy Groups']['site_column_id'])]["value"]
                        intpo_inter_profile = intpo_cell_map[int(config['Associate Int to Policy Groups']['interface_profile_column_id'])]["value"]
                        intpo_access_port_selector = intpo_cell_map[int(config['Associate Int to Policy Groups']['access_port_selector_column_id'])]["value"]
                        intpo_port_block = intpo_cell_map[int(config['Associate Int to Policy Groups']['port_block_column_id'])]["value"]
                        intpo_from_port = int(intpo_cell_map[int(config['Associate Int to Policy Groups']['from_port_column_id'])]["value"])
                        intpo_to_port = int(intpo_cell_map[int(config['Associate Int to Policy Groups']['to_port_column_id'])]["value"])
                        intpo_policy_group = intpo_cell_map[int(config['Associate Int to Policy Groups']['policy_group_name_column_id'])]["value"]
                        intpo_req_id = intpo_cell_map[int(config['Associate Int to Policy Groups']['request_id_column_id'])]["value"]
                        intpo_entry_date = intpo_cell_map[int(config['Associate Int to Policy Groups']['date_of_entry_column_id'])]["value"]
                        intpo_user_email = intpo_cell_map[int(config['Associate Int to Policy Groups']['entered_by_column_id'])]["value"]
                        intpo_provision_date = intpo_cell_map[int(config['Associate Int to Policy Groups']['date_of_provisioning_column_id'])]["value"]

                        intpo_var_fname = "Associate-Int-Policy-Group/interface-to-policygroup-var.yml"
                        intpo_var_stream = open(intpo_var_fname, 'r')
                        intpo_var_data = yaml.load(intpo_var_stream, Loader=yaml.FullLoader)

                        intpo_var_data['interface_to_policy_group'][0]['leaf_interface_profile'] = intpo_inter_profile
                        intpo_var_data['interface_to_policy_group'][0]['access_port_selector'] = intpo_access_port_selector
                        intpo_var_data['interface_to_policy_group'][0]['leaf_port_blk'] = intpo_port_block
                        intpo_var_data['interface_to_policy_group'][0]['from_port'] = intpo_from_port
                        intpo_var_data['interface_to_policy_group'][0]['to_port'] = intpo_to_port
                        intpo_var_data['interface_to_policy_group'][0]['policy_group_name'] = intpo_policy_group

                        temp_intpo_var_fname = "Associate-Int-Policy-Group/interface-to-policygroup-var-"+intpo_req_id+".yml"

                        with open(temp_intpo_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(intpo_var_data, default_flow_style=False, sort_keys=False))

                        intpo_playbook_fname = "Associate-Int-Policy-Group/interface-to-policygroup-playbook.yml"
                        intpos_stream = open(intpo_playbook_fname, 'r')
                        intpo_playbook_data = yaml.load(intpos_stream, Loader=yaml.FullLoader)

                        intpo_playbook_data[0]['hosts'] = apic_controller
                        intpo_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_intpo_var_fname.split("/")[1]

                        temp_intpo_playbook_fname = "Associate-Int-Policy-Group/interface-to-policygroup-playbook-"+intpo_req_id+".yml"

                        with open(temp_intpo_playbook_fname, 'w') as intpo_yaml_file:
                            intpo_yaml_file.write(yaml.dump(intpo_playbook_data, default_flow_style=False, sort_keys=False))

                        cmd = ["ansible-playbook", "-i", "Associate-Int-Policy-Group/inventory.yml", "{}".format(temp_intpo_playbook_fname)]
                        intpo_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = intpo_ansible_output.communicate()

                        intpo_ansible_response = json.loads(stdout.decode('ascii'))

                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if intpo_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate Int to Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif intpo_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate Int to Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif intpo_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Associate Int to Policy Groups']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)
                    else:
                        continue

                # Create Static Path Binding smartsheet webhook triggered
                elif dict_response['sheetId'] == int(config['Create Static Path Binding']['sheet_id']):
                    spb_cell_map = {}
                    for cell in response.cells:
                        if cell.value:
                            display_value = cell.display_value
                            value = cell.value
                            spb_cell_map[cell.column_id] = {
                                "displayValue": display_value,
                                "value": value,
                            }
                    # If ready to deploy checkbox is True, build the var file and ansible playbook
                    if int(config['Create Static Path Binding']['ready_to_deploy_column_id']) in spb_cell_map:
                        apic_controller = spb_cell_map[int(config['Create Static Path Binding']['site_column_id'])]["value"]
                        spb_tenant = spb_cell_map[int(config['Create Static Path Binding']['tenant_column_id'])]["value"]
                        spb_app_profile = spb_cell_map[int(config['Create Static Path Binding']['app_profile_column_id'])]["value"]
                        spb_epg = spb_cell_map[int(config['Create Static Path Binding']['epg_name_column_id'])]["value"]
                        spb_encap = int(spb_cell_map[int(config['Create Static Path Binding']['encapsulation_id_column_id'])]["value"])
                        spb_interface = spb_cell_map[int(config['Create Static Path Binding']['interface_column_id'])]["value"].lstrip("eth")
                        spb_interface_type = spb_cell_map[int(config['Create Static Path Binding']['interface_type_column_id'])]["value"]
                        spb_leaf_range = int(spb_cell_map[int(config['Create Static Path Binding']['leaf_range_column_id'])]["value"])
                        spb_interface_mode = spb_cell_map[int(config['Create Static Path Binding']['interface_mode_column_id'])]["value"]
                        spb_req_id = spb_cell_map[int(config['Create Static Path Binding']['request_id_column_id'])]["value"]
                        spb_entry_date = spb_cell_map[int(config['Create Static Path Binding']['date_of_entry_column_id'])]["value"]
                        spb_user_email = spb_cell_map[int(config['Create Static Path Binding']['entered_by_column_id'])]["value"]
                        spb_provision_date = spb_cell_map[int(config['Create Static Path Binding']['date_of_provisioning_column_id'])]["value"]

                        # Open the var file template in read-only mode
                        spb_var_fname = "Create-Static-Path-Binding/create-static-path-var.yml"
                        spb_var_stream = open(spb_var_fname, 'r')
                        spb_var_data = yaml.load(spb_var_stream, Loader=yaml.FullLoader)

                        # Update the parameters in the yaml var file with the information from the smartsheet
                        spb_var_data['static_paths'][0]['tenant'] = spb_tenant
                        spb_var_data['static_paths'][0]['ap'] = spb_app_profile
                        spb_var_data['static_paths'][0]['epg'] = spb_epg
                        spb_var_data['static_paths'][0]['encap_id'] = spb_encap
                        spb_var_data['static_paths'][0]['interface_mode'] = spb_interface_mode
                        spb_var_data['static_paths'][0]['interface_type'] = spb_interface_type
                        spb_var_data['static_paths'][0]['leaf_range'] = spb_leaf_range
                        spb_var_data['static_paths'][0]['interface'] = spb_interface

                        temp_spb_var_fname = "Create-Static-Path-Binding/create-static-path-var-"+spb_req_id+".yml"

                        # Create a new yaml var file with the values from the smartsheet
                        with open(temp_spb_var_fname, 'w') as yaml_file:
                            yaml_file.write(yaml.dump(spb_var_data, default_flow_style=False, sort_keys=False))

                        # Open the playbook file in read-only mode
                        spb_playbook_fname = "Create-Static-Path-Binding/create-static-path-playbook.yml"
                        spbs_stream = open(spb_playbook_fname, 'r')
                        spb_playbook_data = yaml.load(spbs_stream, Loader=yaml.FullLoader)

                        # Update the parameters in the yaml playbook file with the necessary information
                        spb_playbook_data[0]['hosts'] = apic_controller
                        spb_playbook_data[0]['tasks'][0]['include_vars']['file'] = temp_spb_var_fname.split("/")[1]

                        temp_spb_playbook_fname = "Create-Static-Path-Binding/create-static-path-playbook-"+spb_req_id+".yml"

                        # Create a new yaml playbook file
                        with open(temp_spb_playbook_fname, 'w') as spb_yaml_file:
                            spb_yaml_file.write(yaml.dump(spb_playbook_data, default_flow_style=False, sort_keys=False))

                        # Run the ansible playbook
                        cmd = ["ansible-playbook", "-i", "Create-Static-Path-Binding/inventory.yml", "{}".format(temp_spb_playbook_fname)]
                        spb_ansible_output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        stdout, stderr = spb_ansible_output.communicate()

                        spb_ansible_response = json.loads(stdout.decode('ascii'))

                        print(spb_ansible_response)
                        playbook_url = "https://api.smartsheet.com/2.0/sheets/"+str(dict_response['sheetId'])+"/rows"
                        headers = {
                            'Authorization': 'Bearer '+ config['Environment']['smartsheet_API_key'],
                            'Content-Type': 'application/json'
                            }                    
                        # If the ansible playbook failed - update the ready to deploy cell to red
                        if spb_ansible_response["stats"][apic_controller]["failures"] > 0:
                            red_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Create Static Path Binding']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,27,,,,,,,"
                                }
                                ]
                            })
                            playbook_fail_response = requests.request("PUT", playbook_url, headers=headers, data=red_payload)
                        # If the ansible playbook performed changes - update the ready to deploy cell to orange
                        elif spb_ansible_response["stats"][apic_controller]["changed"] > 0:
                            orange_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Create Static Path Binding']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,28,,,,,,,"
                                }
                                ]
                            })
                            playbook_change_response = requests.request("PUT", playbook_url, headers=headers, data=orange_payload)
                        # If the ansible playbook ran without errors - update the ready to deploy cell to green    
                        elif spb_ansible_response["stats"][apic_controller]["ok"] > 0:
                            green_payload = json.dumps({
                                "id": dict_response["id"],
                                "cells": [{
                                    "columnId": config['Create Static Path Binding']['ready_to_deploy_column_id'],
                                    "value": True,
                                    "format": ",,,,,,,,,30,,,,,,,"
                                }
                                ]
                            })
                            playbook_ok_response = requests.request("PUT", playbook_url, headers=headers, data=green_payload)

                    else:
                        continue

        print("---------------------------------------")

        # return process status to update status sheet (sucess/fail)
        return(["Passed", "Configuration updated successfully"])
