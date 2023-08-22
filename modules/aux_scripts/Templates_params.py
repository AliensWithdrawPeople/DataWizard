from flask import Flask, redirect, url_for

sidebar_urls = {
    'Main' : "index",
    
    # Lab section
    'Lab.tools' : "lab.show_Lab_tools",
    'Lab.add_tool' : "lab.add_tool",
    
    'Lab.templates' : "index",
    
    'Lab.users' : "lab.show_Lab_users",
    'Lab.add_user' : "lab.add_user",
    
    # Organiztions section
    'Organizations' : "index",
    
    # Reports section
    'Reports.cat' : "search.show_Reports_cat",
    'Reports.reestr' : "index",
    'Reports.reports' : "index",
    'Reports.report_total' : "index",
    
    # User info section
    'LogIn' : "auth.login",
    'LogOut' : "auth.logout"
}