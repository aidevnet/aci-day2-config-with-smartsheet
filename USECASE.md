# ACI management simplification using Smartsheets

The ACI management simplification with Python use case offers ACI data center administrators a simple and intuitive interface for interacting and managing their data center infrastructure. Using smartsheets and forms from https://www.smartsheet.com as input and collection of data points, data center administrators can automate and simplify the configuration of ACI fabrics using the Python code in this repo. The ACI APIC GUI interface can be intimidating and confusing, especially for technicians and engineers that are just getting started with managing ACI. The main purpose of this use case is to simplify this interaction and to make it easier for ACI administrators to manage data center infrastructure. We have decided to cover eight common day to day ACI management activities in our use case:

    Deploy an application
    Create static path bindings
    Configure filters
    Configure contracts
    Configure policy groups
    Configure switch interface profiles
    Associate interfaces to policy groups
    Associate EPGs to contracts

Additional ACI management activities similar to the ones above can be easily created by extending the Python code in this repo.

    Technology stack: Python, Ansible, Cisco ACI, REST APIs, Smartsheet API, HTML/CSS, JavaScript
    
# DevNet Sandbox

[Cisco ACI reservable sandbox](https://devnetsandbox.cisco.com/RM/Diagram/Index/661da090-c16c-4b8c-95db-1194e461964c?diagramType=Topology)

[Always-on ACI simulator](https://devnetsandbox.cisco.com/RM/Diagram/Index/5a229a7c-95d5-4cfd-a651-5ee9bc1b30e2?diagramType=Topology)
