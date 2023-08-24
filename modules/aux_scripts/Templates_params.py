from flask import Flask, redirect, url_for

sidebar_urls = {
    'Main' : "index",
    
    # Lab section
    'Lab.tools' : "lab.show_Lab_tools",
    'Lab.add_tool' : "lab.add_tool",
    'Lab.edit_tool' : "lab.edit_tool",
    
    'Lab.templates' : "index",
    
    'Lab.users' : "lab.show_Lab_users",
    'Lab.add_user' : "lab.add_user",
    'Lab.edit_user' : "lab.edit_user",
    
    # Organiztions section
    'Organizations' : "organizations.orgs",
    'Organizations.Add_org' : "organizations.add_company",
    
    # Reports section
    'Reports.cat' : "search.show_Reports_cat",
    'Reports.reestr' : "index",
    'Reports.reports' : "index",
    'Reports.report_total' : "index",
    
    # User info section
    'LogIn' : "auth.login",
    'LogOut' : "auth.logout"
}