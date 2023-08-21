from flask import Flask, redirect, url_for

sidebar_urls = {
    'Main' : "index",
    'Lab.tools' : "index",
    'Lab.templates' : "index",
    'Lab.users' : "lab.show_Lab_users",
    'Lab.add_user' : "lab.add_user",
    'Organizations' : "index",
    'Reports.cat' : "search.show_Reports_cat",
    'Reports.reestr' : "index",
    'Reports.reports' : "index",
    'Reports.report_total' : "index",
    'LogOut' : "index"
}