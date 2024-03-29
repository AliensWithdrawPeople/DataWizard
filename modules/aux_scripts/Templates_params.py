sidebar_urls = {
    'Main' : "index",
    
    # Lab section
    'Lab.tools' : "lab.show_Lab_tools",
    'Lab.add_tool' : "lab.add_tool",
    'Lab.edit_tool' : "lab.edit_tool",
    # TODO: Add Lab.templates page
    'Lab.templates' : "index",
    
    'Lab.users' : "lab.show_Lab_users",
    'Lab.add_user' : "lab.add_user",
    'Lab.edit_user' : "lab.edit_user",
    
    # Organiztions section
    'Organizations' : "organizations.orgs",
    'Organizations.add_org' : "organizations.add_company",
    'Organizations.edit_org' : "organizations.edit_company",
    'Organizations.add_unit' : "organizations.add_unit",
    'Organizations.edit_unit' : "organizations.edit_unit",
    'Organizations.load_units_from_DB' : "organizations.get_units",
    
    # Reports section
    'Reports.cat' : "base_report.catalogue.cat",
    'Reports.add_cat' : "base_report.catalogue.add_cat",
    'Reports.edit_cat' : "base_report.catalogue.edit_cat",
    
    'Reports.hardware' : "base_report.hardware.hardware_list",
    'Reports.edit_hardware' : "base_report.hardware.edit_hardware",
    'Reports.add_hardware' : "base_report.hardware.add_hardware",
    'Reports.hardware.load_type_data_from_DB' : "base_report.hardware.get_hardware_type_info",
    
    'Reports.reports' : "base_report.reports.current_reports",
    'Reports.create_reports' : "base_report.reports.send_reports",
    'Reports.add_report' : "base_report.reports.add_report",
    'Reports.edit_report' : "base_report.reports.edit_report",
    'Reports.load_hardware_data_from_DB' : "base_report.reports.get_hardware_info",
    # TODO: Add Reports.report_total page
    'Reports.report_total' : "index",
    
    # User info section
    'LogIn' : "auth.login",
    'LogOut' : "auth.logout"
}