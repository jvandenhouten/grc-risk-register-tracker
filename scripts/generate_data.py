"""
generate_data.py
=================
Builds the synthetic GRC Risk Register & Controls Tracker database.

This script generates a realistic, internally-consistent risk register for a
fictional mid-size organization ("Atlas Meridian Group" — a logistics,
industrial services, and international security-consulting company
headquartered in Austin, TX, with field operations across Texas and a
regional office in Riyadh, Saudi Arabia) and maps its controls to the NIST
Cybersecurity Framework (CSF) 2.0.

ALL DATA IN THIS PROJECT IS SYNTHETIC. "Atlas Meridian Group" is a fictional
company; no real organization, employer, or individual's confidential
information is represented here. The dataset exists to demonstrate GRC data
modeling, risk-scoring methodology, and dashboard/analysis design.

Design discipline (mirrored throughout the project):
  - OBSERVED FACTS: control implementation status, assessment findings,
    remediation status. These are direct, recorded observations.
  - ANALYTICAL JUDGMENT: residual risk scores. Every residual risk score
    carries an analyst-authored rationale and is kept in a separate table
    from the observed facts it is based on, so a reader can always trace a
    judgment call back to the evidence that informed it.

Run:
    python scripts/generate_data.py
Produces:
    data/grc_register.db
"""

import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproducible dataset

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "grc_register.db"
SCHEMA_PATH = ROOT / "scripts" / "schema.sql"
CSF_REFERENCE_PATH = ROOT / "data" / "csf2_reference.json"

TODAY = date(2026, 9, 1)


# ============================================================================
# Reference / dimension data
# ============================================================================

BUSINESS_UNITS = [
    ("Corporate HQ & Executive Leadership", "Austin, TX", "Executive leadership, legal, and enterprise governance functions."),
    ("Information Technology & Cybersecurity", "Austin, TX", "Enterprise IT infrastructure, applications, and cybersecurity program."),
    ("Field Operations - Central Texas", "Austin, TX", "Regional delivery, warehousing support, and field service operations."),
    ("Field Operations - Gulf Coast", "Houston, TX", "Regional delivery and industrial services operations."),
    ("Warehousing & Logistics", "San Marcos, TX", "Distribution center operations, inventory, and fleet logistics."),
    ("MENA Regional Office", "Riyadh, Saudi Arabia", "International business development and operations across the Middle East / North Africa region."),
    ("Human Resources & Talent", "Austin, TX", "Talent acquisition, employee relations, and HR systems."),
    ("Finance & Accounting", "Austin, TX", "Corporate finance, accounts payable/receivable, and payroll."),
]

# (name, asset_type, business_unit_index, criticality, description)
ASSETS = [
    ("Enterprise Resource Planning (ERP) System", "Application", 7, "Critical", "Core financial management and general ledger system."),
    ("HR Information System (HRIS)", "Application", 6, "High", "System of record for employee data, benefits, and payroll inputs."),
    ("Fleet Telematics Platform", "Application", 3, "High", "GPS tracking, driver behavior, and vehicle diagnostics for the delivery fleet."),
    ("Warehouse Management System (WMS)", "Application", 4, "High", "Inventory control and distribution center operations system."),
    ("Corporate Email & Collaboration Suite", "Application", 1, "Critical", "Enterprise email, chat, and document collaboration platform."),
    ("Customer Relationship Management (CRM) System", "Application", 0, "Medium", "Sales pipeline and customer account management."),
    ("Employee PII Data Store", "Data Store", 6, "Critical", "Repository of employee personal data underlying the HRIS."),
    ("Customer & Contract Records Repository", "Data Store", 0, "High", "Repository of customer contracts and commercial agreements."),
    ("Payroll & Banking Data Store", "Data Store", 7, "Critical", "Employee banking and payroll processing data."),
    ("Austin Corporate Headquarters", "Facility", 0, "High", "Primary corporate office and executive operations."),
    ("San Marcos Distribution Center", "Facility", 4, "High", "Primary warehousing and distribution facility."),
    ("Houston Field Office", "Facility", 3, "Medium", "Regional field operations office and dispatch center."),
    ("Riyadh Regional Office", "Facility", 5, "Critical", "International office supporting MENA business operations."),
    ("Corporate Network / Data Center", "Infrastructure", 1, "Critical", "On-premises network core and primary data center."),
    ("Cloud Hosting Environment (AWS)", "Infrastructure", 1, "Critical", "Primary cloud infrastructure hosting production applications."),
    ("VPN & Remote Access Infrastructure", "Infrastructure", 1, "High", "Remote access gateway for employees and field staff."),
    ("Physical Access Control System", "Infrastructure", 1, "High", "Badge access and CCTV infrastructure across facilities."),
    ("Third-Party Payroll Processor", "Third Party", 7, "High", "Outsourced payroll processing vendor."),
    ("Third-Party Background Check Vendor", "Third Party", 6, "Medium", "Vendor performing pre-employment background screening."),
    ("Third-Party MENA Security Escort Provider", "Third Party", 5, "High", "Contracted provider of security escort services in the MENA region."),
    ("Cloud Backup & Disaster Recovery Vendor", "Third Party", 1, "High", "Managed backup and DR service provider."),
    ("Delivery Fleet - Central Texas", "Fleet / Equipment", 2, "Medium", "Company-owned and leased delivery vehicles, Central Texas region."),
    ("Delivery Fleet - Gulf Coast", "Fleet / Equipment", 3, "Medium", "Company-owned and leased delivery vehicles, Gulf Coast region."),
    ("New Hire Onboarding Process", "Process", 6, "Low", "Employee onboarding, provisioning, and orientation process."),
    ("Vendor Onboarding & Due Diligence Process", "Process", 0, "Medium", "Process for evaluating and approving new third-party vendors."),
    ("Incident Reporting & Escalation Process", "Process", 0, "High", "Cross-functional process for reporting and escalating security/safety incidents."),
    ("DOT Compliance & Driver Qualification Process", "Process", 4, "High", "Process ensuring driver qualification files meet DOT requirements."),
    ("Expatriate Duty-of-Care Program", "Process", 5, "Critical", "Program governing safety and support for personnel deployed to MENA."),
]

BU_NAMES = [b[0] for b in BUSINESS_UNITS]
ASSET_NAMES = [a[0] for a in ASSETS]

OWNERS = [
    "VP, Enterprise Risk & Compliance", "Chief Information Security Officer", "Director of IT Operations",
    "Director of Field Operations", "Director of Warehousing & Logistics", "MENA Regional Director",
    "VP, Human Resources", "Controller, Finance & Accounting", "Director of Physical Security",
    "Director of Safety & EHS", "General Counsel", "Director of Fleet Operations",
]

ASSESSORS = ["Internal Audit", "3rd-Party Assessor (Meridian Assurance Partners)", "GRC Analyst", "CISO Office"]
ANALYSTS = ["Sr. Risk Analyst - J. Whitfield", "Sr. Risk Analyst - M. Okafor", "GRC Manager - R. Delgado", "CISO Office"]


# ============================================================================
# Risk register — 45 curated, realistic risks across six categories
# Each: (title, description, category, asset_name or None, business_unit_name, owner)
# ============================================================================

RISKS = [
    # --- Cybersecurity (12) ---
    ("Ransomware compromise of corporate file shares and backups",
     "A successful ransomware attack could encrypt production file shares and, if backups are not adequately isolated, compromise recovery capability.",
     "Cybersecurity", "Corporate Network / Data Center", "Information Technology & Cybersecurity", "Chief Information Security Officer"),
    ("Phishing-enabled business email compromise (BEC) targeting Finance",
     "Accounts Payable staff are a recurring target for invoice-fraud phishing; a successful compromise could result in fraudulent wire transfers.",
     "Cybersecurity", "Corporate Email & Collaboration Suite", "Finance & Accounting", "Controller, Finance & Accounting"),
    ("Unpatched internet-facing VPN appliance",
     "The remote-access VPN appliance has a history of delayed patch cycles, increasing exposure to known, actively exploited vulnerabilities.",
     "Cybersecurity", "VPN & Remote Access Infrastructure", "Information Technology & Cybersecurity", "Director of IT Operations"),
    ("Weak / reused administrative credentials on core network infrastructure",
     "Shared local administrator credentials on network devices have not been rotated on a defined schedule.",
     "Cybersecurity", "Corporate Network / Data Center", "Information Technology & Cybersecurity", "Director of IT Operations"),
    ("Lack of multi-factor authentication enforcement for privileged accounts",
     "A subset of privileged/administrative accounts are not yet enrolled in mandatory multi-factor authentication.",
     "Cybersecurity", "Corporate Network / Data Center", "Information Technology & Cybersecurity", "Chief Information Security Officer"),
    ("Cloud storage misconfiguration exposing customer contract data",
     "Periodic cloud configuration reviews have identified storage buckets with overly permissive access policies.",
     "Cybersecurity", "Cloud Hosting Environment (AWS)", "Information Technology & Cybersecurity", "Chief Information Security Officer"),
    ("Insufficient logging and monitoring delaying intrusion detection",
     "Centralized log collection does not yet cover all critical systems, extending the likely time-to-detect for an intrusion.",
     "Cybersecurity", "Corporate Network / Data Center", "Information Technology & Cybersecurity", "Chief Information Security Officer"),
    ("Legacy Warehouse Management System on an unsupported OS version",
     "The WMS application server runs on an operating system version that has reached end-of-support, limiting available security patches.",
     "Cybersecurity", "Warehouse Management System (WMS)", "Warehousing & Logistics", "Director of IT Operations"),
    ("Insider data exfiltration risk from departing employees",
     "Access deprovisioning for departing employees is not consistently completed within the target window, extending the window for potential data exfiltration.",
     "Cybersecurity", "Employee PII Data Store", "Human Resources & Talent", "VP, Human Resources"),
    ("Third-party vendor remote access without adequate network segmentation",
     "Several vendors retain standing remote access to internal systems without dedicated, segmented access paths.",
     "Cybersecurity", "VPN & Remote Access Infrastructure", "Information Technology & Cybersecurity", "Director of IT Operations"),
    ("Inadequate endpoint detection and response coverage on field laptops",
     "EDR agent deployment on field-issued laptops lags behind corporate-issued devices.",
     "Cybersecurity", "Corporate Network / Data Center", "Information Technology & Cybersecurity", "Chief Information Security Officer"),
    ("Shadow IT: unsanctioned cloud applications used by business units",
     "Business units have adopted cloud collaboration tools outside of IT's sanctioned application list, creating unmanaged data-security exposure.",
     "Cybersecurity", "Cloud Hosting Environment (AWS)", "Corporate HQ & Executive Leadership", "Chief Information Security Officer"),

    # --- Physical Security (8) ---
    ("Inadequate perimeter access controls at San Marcos Distribution Center",
     "Perimeter fencing and vehicle-gate access controls at the distribution center have known gaps identified in the most recent physical security survey.",
     "Physical Security", "San Marcos Distribution Center", "Warehousing & Logistics", "Director of Physical Security"),
    ("Elevated threat environment surrounding Riyadh Regional Office operations",
     "Personnel and operations at the Riyadh office face a materially different, more dynamic threat environment than domestic facilities.",
     "Physical Security", "Riyadh Regional Office", "MENA Regional Office", "MENA Regional Director"),
    ("Tailgating / unauthorized facility access at Austin HQ",
     "Badge-access tailgating has been observed at HQ entrances during periods of high foot traffic.",
     "Physical Security", "Austin Corporate Headquarters", "Corporate HQ & Executive Leadership", "Director of Physical Security"),
    ("Insufficient CCTV coverage at Houston Field Office loading docks",
     "Camera coverage does not fully capture loading-dock activity, limiting evidentiary value in the event of a theft or safety incident.",
     "Physical Security", "Houston Field Office", "Field Operations - Gulf Coast", "Director of Physical Security"),
    ("Lost or unrevoked physical access badges for terminated employees",
     "Badge deactivation for terminated employees is not always completed same-day, leaving a window during which a lost or retained badge remains active.",
     "Physical Security", "Physical Access Control System", "Human Resources & Talent", "Director of Physical Security"),
    ("Lack of standardized executive protection protocol for MENA travel",
     "Executive and senior staff travel to the MENA region does not follow a formalized, risk-tiered protective protocol.",
     "Physical Security", "Riyadh Regional Office", "MENA Regional Office", "MENA Regional Director"),
    ("Inadequate visitor management and escort procedures at HQ",
     "Visitor sign-in and escort procedures at Austin HQ are inconsistently followed, increasing unauthorized-access risk.",
     "Physical Security", "Austin Corporate Headquarters", "Corporate HQ & Executive Leadership", "Director of Physical Security"),
    ("Cargo theft risk during last-mile delivery, Gulf Coast region",
     "The Gulf Coast delivery region has an elevated rate of reported cargo theft attempts relative to other regions.",
     "Physical Security", "Delivery Fleet - Gulf Coast", "Field Operations - Gulf Coast", "Director of Fleet Operations"),

    # --- Operational (8) ---
    ("Single point of failure in fleet telematics platform vendor",
     "Fleet routing and driver-safety monitoring depend on a single telematics vendor with no evaluated failover option.",
     "Operational", "Fleet Telematics Platform", "Warehousing & Logistics", "Director of Fleet Operations"),
    ("Inadequate business continuity plan for San Marcos DC outage",
     "The distribution center's continuity plan has not been tested against a full-facility outage scenario.",
     "Operational", "San Marcos Distribution Center", "Warehousing & Logistics", "Director of Warehousing & Logistics"),
    ("Key-person dependency risk in MENA regional leadership",
     "MENA regional operations rely heavily on a small number of individuals without a documented succession or cross-training plan.",
     "Operational", "Riyadh Regional Office", "MENA Regional Office", "MENA Regional Director"),
    ("Supply chain disruption from sole-sourced logistics partner",
     "A significant share of long-haul freight capacity is sole-sourced, with limited contingency arrangements.",
     "Operational", "Delivery Fleet - Gulf Coast", "Field Operations - Gulf Coast", "Director of Field Operations"),
    ("Inconsistent incident reporting and escalation across regions",
     "Field incident reports are captured using different formats and timeliness standards across regions, delaying enterprise visibility.",
     "Operational", "Incident Reporting & Escalation Process", "Corporate HQ & Executive Leadership", "VP, Enterprise Risk & Compliance"),
    ("Inadequate succession planning for critical operations roles",
     "Several operations leadership roles lack a documented succession plan or identified backup.",
     "Operational", "Corporate HQ & Executive Leadership", "Corporate HQ & Executive Leadership", "VP, Human Resources"),
    ("Data quality issues in WMS impacting inventory accuracy",
     "Recurring data-entry inconsistencies in the WMS have led to periodic inventory count discrepancies.",
     "Operational", "Warehouse Management System (WMS)", "Warehousing & Logistics", "Director of Warehousing & Logistics"),
    ("Fleet maintenance backlog increasing breakdown and downtime risk",
     "A backlog of scheduled preventive-maintenance work orders has grown across the Central Texas delivery fleet.",
     "Operational", "Delivery Fleet - Central Texas", "Field Operations - Central Texas", "Director of Fleet Operations"),

    # --- Third-Party (6) ---
    ("Inadequate due diligence on new vendor onboarding",
     "New vendors are not consistently subject to a standardized security and financial due-diligence review before onboarding.",
     "Third-Party", "Vendor Onboarding & Due Diligence Process", "Corporate HQ & Executive Leadership", "VP, Enterprise Risk & Compliance"),
    ("Payroll processor lacks a current SOC 2 attestation on file",
     "The organization does not have a current SOC 2 Type II report on file for its outsourced payroll processor.",
     "Third-Party", "Third-Party Payroll Processor", "Finance & Accounting", "Controller, Finance & Accounting"),
    ("MENA security escort provider vetting gaps",
     "The vetting and performance-monitoring process for the contracted MENA security escort provider is not formally documented.",
     "Third-Party", "Third-Party MENA Security Escort Provider", "MENA Regional Office", "MENA Regional Director"),
    ("Cloud backup and disaster-recovery vendor concentration risk",
     "Both primary hosting and backup/DR services are provided within the same cloud provider's ecosystem, reducing independence of the recovery path.",
     "Third-Party", "Cloud Backup & Disaster Recovery Vendor", "Information Technology & Cybersecurity", "Director of IT Operations"),
    ("Background-check vendor data-handling practices unverified",
     "The organization has not independently verified the data-handling and retention practices of its background-check vendor.",
     "Third-Party", "Third-Party Background Check Vendor", "Human Resources & Talent", "VP, Human Resources"),
    ("Subcontractor access to customer facilities not contractually bound to security requirements",
     "Some subcontractor agreements do not flow down the organization's minimum security requirements to personnel with customer-site access.",
     "Third-Party", "Vendor Onboarding & Due Diligence Process", "Corporate HQ & Executive Leadership", "General Counsel"),

    # --- Compliance / Regulatory (6) ---
    ("DOT driver qualification file gaps across Field Operations",
     "A sample audit of driver qualification files identified missing or expired documentation for a subset of drivers.",
     "Compliance / Regulatory", "DOT Compliance & Driver Qualification Process", "Field Operations - Central Texas", "Director of Field Operations"),
    ("Incomplete data privacy program relative to state privacy law requirements",
     "The organization's data privacy program has not been fully mapped against applicable state consumer/employee privacy statutes.",
     "Compliance / Regulatory", "Employee PII Data Store", "Corporate HQ & Executive Leadership", "General Counsel"),
    ("Export control and sanctions compliance gaps for MENA operations",
     "MENA business development activity has not been subject to a formal, documented export-control and sanctions screening process.",
     "Compliance / Regulatory", "Riyadh Regional Office", "MENA Regional Office", "General Counsel"),
    ("Inconsistent employment-eligibility verification recordkeeping",
     "Form I-9 recordkeeping practices vary across hiring locations, with some files incomplete or improperly retained.",
     "Compliance / Regulatory", "New Hire Onboarding Process", "Human Resources & Talent", "VP, Human Resources"),
    ("Insufficient documentation supporting OSHA recordkeeping requirements",
     "OSHA 300/300A recordkeeping is maintained inconsistently across warehousing and field locations.",
     "Compliance / Regulatory", "San Marcos Distribution Center", "Warehousing & Logistics", "Director of Safety & EHS"),
    ("Contractual data-protection obligations not consistently flowed to vendors",
     "Standard data-protection clauses are not consistently included in vendor contracts executed outside of central procurement.",
     "Compliance / Regulatory", "Vendor Onboarding & Due Diligence Process", "Corporate HQ & Executive Leadership", "General Counsel"),

    # --- Safety / EHS (5) ---
    ("Warehouse forklift operation safety gaps at San Marcos DC",
     "A recent safety walkthrough identified inconsistent adherence to forklift operating procedures and pedestrian separation.",
     "Safety / EHS", "San Marcos Distribution Center", "Warehousing & Logistics", "Director of Safety & EHS"),
    ("Driver fatigue and hours-of-service risk on long-haul routes",
     "Hours-of-service logs show a pattern of drivers approaching regulatory duty-time limits on select long-haul routes.",
     "Safety / EHS", "Delivery Fleet - Gulf Coast", "Field Operations - Gulf Coast", "Director of Safety & EHS"),
    ("Inadequate emergency evacuation planning at Riyadh Regional Office",
     "The Riyadh office does not have a documented, drilled emergency evacuation plan tailored to local conditions.",
     "Safety / EHS", "Riyadh Regional Office", "MENA Regional Office", "MENA Regional Director"),
    ("Heat-related illness risk for outdoor field crews during Texas summer operations",
     "Field crews performing outdoor work during peak summer months face elevated heat-illness risk without a formalized prevention program.",
     "Safety / EHS", "Delivery Fleet - Central Texas", "Field Operations - Central Texas", "Director of Safety & EHS"),
    ("Incomplete PPE compliance in warehouse operations",
     "Personal protective equipment compliance checks at the distribution center show inconsistent adherence.",
     "Safety / EHS", "San Marcos Distribution Center", "Warehousing & Logistics", "Director of Safety & EHS"),
]


# ============================================================================
# Controls — 50 controls mapped to NIST CSF 2.0 categories
# Each: (name, description, control_type, category_id, owner)
# ============================================================================

CONTROLS = [
    # GV.OC
    ("Enterprise Risk Register & Business Context Documentation", "Maintained, centrally-owned risk register documenting organizational context, mission-critical services, and stakeholder dependencies.", "Preventive", "GV.OC", "VP, Enterprise Risk & Compliance"),
    ("Stakeholder & Legal/Regulatory Requirements Inventory", "Documented inventory of applicable legal, regulatory, and contractual cybersecurity/privacy obligations, reviewed annually.", "Preventive", "GV.OC", "General Counsel"),
    # GV.RM
    ("Enterprise Risk Management Policy & Risk Appetite Statement", "Board-approved policy establishing risk appetite, tolerance thresholds, and escalation criteria.", "Preventive", "GV.RM", "VP, Enterprise Risk & Compliance"),
    ("Quarterly Risk Committee Review", "Cross-functional risk committee reviews the risk register and residual risk trends on a quarterly cadence.", "Detective", "GV.RM", "VP, Enterprise Risk & Compliance"),
    # GV.RR
    ("RACI for Cybersecurity & Risk Roles", "Documented responsibility matrix defining accountability for cybersecurity and risk management activities.", "Preventive", "GV.RR", "Chief Information Security Officer"),
    ("Named Data Protection / Privacy Officer", "Formally designated individual accountable for data protection and privacy compliance.", "Preventive", "GV.RR", "General Counsel"),
    # GV.PO
    ("Information Security Policy Suite", "Board-approved suite of information security policies covering access control, data handling, and acceptable use.", "Preventive", "GV.PO", "Chief Information Security Officer"),
    ("DOT Driver Qualification File Management Program", "Documented program governing collection, verification, and retention of DOT driver qualification files.", "Preventive", "GV.PO", "Director of Field Operations"),
    ("OSHA Recordkeeping & EHS Management Program", "Documented program governing OSHA-required recordkeeping and EHS incident tracking.", "Preventive", "GV.PO", "Director of Safety & EHS"),
    ("Forklift & Warehouse Equipment Safety Program", "Documented safety program covering forklift certification, pedestrian separation, and equipment inspection.", "Preventive", "GV.PO", "Director of Safety & EHS"),
    ("Heat Illness Prevention Program", "Documented program governing hydration, rest-cycle, and monitoring requirements for outdoor field work in high-heat conditions.", "Preventive", "GV.PO", "Director of Safety & EHS"),
    # GV.OV
    ("Board/Executive Risk Reporting Cadence", "Recurring executive and board-level reporting on enterprise risk posture and key risk indicators.", "Detective", "GV.OV", "VP, Enterprise Risk & Compliance"),
    ("Internal Audit Program for Cyber & Compliance Controls", "Internal audit function performs periodic testing of key cyber and compliance controls.", "Detective", "GV.OV", "VP, Enterprise Risk & Compliance"),
    # GV.SC
    ("Vendor Risk Management Program", "Documented program for tiering, assessing, and monitoring third-party vendor risk.", "Preventive", "GV.SC", "VP, Enterprise Risk & Compliance"),
    ("Third-Party Security Assessment Questionnaire Process", "Standardized security questionnaire administered to vendors prior to onboarding and periodically thereafter.", "Detective", "GV.SC", "Chief Information Security Officer"),
    # ID.AM
    ("IT Asset Inventory & CMDB", "Maintained configuration management database tracking hardware, software, and system ownership.", "Preventive", "ID.AM", "Director of IT Operations"),
    ("Data Classification & Inventory", "Program to classify and inventory sensitive data across applications and data stores.", "Preventive", "ID.AM", "Chief Information Security Officer"),
    # ID.RA
    ("Annual Enterprise Risk Assessment", "Formal, organization-wide risk assessment performed at least annually.", "Detective", "ID.RA", "VP, Enterprise Risk & Compliance"),
    ("Vulnerability Scanning Program", "Recurring automated vulnerability scanning of internal and internet-facing systems.", "Detective", "ID.RA", "Chief Information Security Officer"),
    # ID.IM
    ("Lessons-Learned / Post-Incident Improvement Process", "Structured post-incident review process feeding identified improvements back into risk and control owners.", "Corrective", "ID.IM", "VP, Enterprise Risk & Compliance"),
    # PR.AA
    ("Multi-Factor Authentication for Privileged & Remote Access", "MFA required for all privileged accounts and remote access sessions.", "Preventive", "PR.AA", "Chief Information Security Officer"),
    ("Role-Based Access Control (RBAC) & Least Privilege", "Access to systems is provisioned according to defined roles with least-privilege enforcement.", "Preventive", "PR.AA", "Director of IT Operations"),
    ("Quarterly Access Recertification", "System owners recertify user access rights on a quarterly basis.", "Detective", "PR.AA", "Director of IT Operations"),
    ("Physical Badge Access & Visitor Management System", "Badge-based access control and visitor sign-in/escort system deployed across facilities.", "Preventive", "PR.AA", "Director of Physical Security"),
    ("Badge/Credential Deprovisioning on Termination", "Same-day deactivation of physical and logical access credentials upon employee termination.", "Preventive", "PR.AA", "Director of Physical Security"),
    # PR.AT
    ("Annual Security Awareness Training", "Mandatory annual training covering phishing, data handling, and acceptable use for all employees.", "Preventive", "PR.AT", "Chief Information Security Officer"),
    ("Phishing Simulation Program", "Recurring simulated phishing campaigns with targeted follow-up training.", "Detective", "PR.AT", "Chief Information Security Officer"),
    # PR.DS
    ("Data Encryption at Rest and in Transit", "Encryption standards applied to sensitive data stores and transmission channels.", "Preventive", "PR.DS", "Director of IT Operations"),
    ("Data Loss Prevention (DLP) Controls", "Automated controls to detect and prevent unauthorized transmission of sensitive data.", "Preventive", "PR.DS", "Chief Information Security Officer"),
    ("Backup & Recovery Program", "Regular, tested backups of critical systems and data with defined retention and isolation requirements.", "Preventive", "PR.DS", "Director of IT Operations"),
    # PR.PS
    ("Endpoint Detection & Response (EDR) Deployment", "EDR agents deployed across corporate and field-issued endpoints with centralized alerting.", "Detective", "PR.PS", "Chief Information Security Officer"),
    ("Patch & Vulnerability Management Program", "Documented patching cadence and vulnerability remediation SLAs by system criticality.", "Preventive", "PR.PS", "Director of IT Operations"),
    ("Cargo Security & Chain-of-Custody Procedures", "Standardized cargo handling, sealing, and chain-of-custody procedures for last-mile delivery.", "Preventive", "PR.PS", "Director of Fleet Operations"),
    # PR.IR
    ("Network Segmentation", "Network architecture segments critical systems, vendor access, and general user traffic.", "Preventive", "PR.IR", "Director of IT Operations"),
    ("Business Continuity & Disaster Recovery Plan", "Documented, periodically tested continuity and disaster recovery plans for critical facilities and systems.", "Preventive", "PR.IR", "VP, Enterprise Risk & Compliance"),
    ("MENA Executive Protection & Duty-of-Care Protocol", "Risk-tiered protective protocol governing personnel travel, movement, and support in the MENA region.", "Preventive", "PR.IR", "MENA Regional Director"),
    # DE.CM
    ("Security Information & Event Management (SIEM) Monitoring", "Centralized log aggregation and correlation across critical systems with 24/7 alerting.", "Detective", "DE.CM", "Chief Information Security Officer"),
    ("CCTV Coverage Standard for Distribution Facilities", "Defined minimum CCTV coverage standard applied across distribution and field facilities.", "Detective", "DE.CM", "Director of Physical Security"),
    # DE.AE
    ("Security Alert Triage & Analysis Process", "Documented process and staffing model for triaging and analyzing security alerts.", "Detective", "DE.AE", "Chief Information Security Officer"),
    # RS.MA
    ("Incident Response Plan", "Documented, tested incident response plan with defined roles and escalation paths.", "Corrective", "RS.MA", "Chief Information Security Officer"),
    ("24/7 Incident Escalation Hotline", "Always-available hotline for reporting security, safety, and operational incidents.", "Detective", "RS.MA", "VP, Enterprise Risk & Compliance"),
    # RS.AN
    ("Digital Forensics & Root Cause Analysis Capability", "Access to internal or contracted digital forensics capability to support incident investigation.", "Corrective", "RS.AN", "Chief Information Security Officer"),
    # RS.CO
    ("Regulatory Breach Notification Procedure", "Documented procedure ensuring timely, compliant notification following a qualifying data breach.", "Corrective", "RS.CO", "General Counsel"),
    # RS.MI
    ("Endpoint Isolation / Containment Playbooks", "Documented playbooks for isolating and containing compromised endpoints during an active incident.", "Corrective", "RS.MI", "Chief Information Security Officer"),
    # RC.RP
    ("Disaster Recovery Runbooks & Failover Testing", "Documented DR runbooks with periodic failover testing for critical systems.", "Corrective", "RC.RP", "Director of IT Operations"),
    ("Warehouse Facility Continuity Plan", "Documented continuity plan for restoring distribution center operations following a disruptive event.", "Corrective", "RC.RP", "Director of Warehousing & Logistics"),
    # RC.CO
    ("Customer & Stakeholder Recovery Communication Plan", "Documented plan for communicating with customers and stakeholders during recovery from a disruptive event.", "Corrective", "RC.CO", "VP, Enterprise Risk & Compliance"),
    # RC.IM
    ("Post-Incident / Post-Exercise Improvement Tracking", "Tracked action items arising from post-incident reviews and continuity/DR exercises.", "Corrective", "RC.IM", "VP, Enterprise Risk & Compliance"),
    # A few additional PR.AA / GV.SC controls to round out coverage
    ("Vendor Remote Access Segmentation", "Dedicated, monitored access paths for third-party vendors requiring remote system access.", "Preventive", "PR.AA", "Director of IT Operations"),
    ("Vendor Onboarding Due Diligence Checklist", "Standardized due-diligence checklist applied prior to approving a new vendor relationship.", "Preventive", "GV.SC", "VP, Enterprise Risk & Compliance"),
]


# ============================================================================
# Risk -> Control mapping (by index into RISKS / CONTROLS, 0-based)
# ============================================================================

def build_control_index(controls):
    return {c[0]: i for i, c in enumerate(controls)}


RISK_CONTROL_MAP = {
    0: ["Backup & Recovery Program", "Endpoint Detection & Response (EDR) Deployment", "Incident Response Plan"],
    1: ["Annual Security Awareness Training", "Phishing Simulation Program", "Multi-Factor Authentication for Privileged & Remote Access"],
    2: ["Patch & Vulnerability Management Program", "Vulnerability Scanning Program"],
    3: ["Multi-Factor Authentication for Privileged & Remote Access", "Role-Based Access Control (RBAC) & Least Privilege"],
    4: ["Multi-Factor Authentication for Privileged & Remote Access"],
    5: ["Data Classification & Inventory", "Data Loss Prevention (DLP) Controls"],
    6: ["Security Information & Event Management (SIEM) Monitoring", "Security Alert Triage & Analysis Process"],
    7: ["Patch & Vulnerability Management Program", "IT Asset Inventory & CMDB"],
    8: ["Badge/Credential Deprovisioning on Termination", "Role-Based Access Control (RBAC) & Least Privilege"],
    9: ["Vendor Remote Access Segmentation", "Network Segmentation"],
    10: ["Endpoint Detection & Response (EDR) Deployment"],
    11: ["Data Classification & Inventory", "Vendor Risk Management Program"],
    12: ["Physical Badge Access & Visitor Management System", "CCTV Coverage Standard for Distribution Facilities"],
    13: ["MENA Executive Protection & Duty-of-Care Protocol"],
    14: ["Physical Badge Access & Visitor Management System"],
    15: ["CCTV Coverage Standard for Distribution Facilities"],
    16: ["Badge/Credential Deprovisioning on Termination"],
    17: ["MENA Executive Protection & Duty-of-Care Protocol"],
    18: ["Physical Badge Access & Visitor Management System"],
    19: ["Cargo Security & Chain-of-Custody Procedures"],
    20: ["Business Continuity & Disaster Recovery Plan", "Vendor Risk Management Program"],
    21: ["Warehouse Facility Continuity Plan", "Business Continuity & Disaster Recovery Plan"],
    22: ["Post-Incident / Post-Exercise Improvement Tracking"],
    23: ["Vendor Risk Management Program", "Business Continuity & Disaster Recovery Plan"],
    24: ["24/7 Incident Escalation Hotline", "Lessons-Learned / Post-Incident Improvement Process"],
    25: ["RACI for Cybersecurity & Risk Roles"],
    26: ["Data Classification & Inventory", "IT Asset Inventory & CMDB"],
    27: ["Patch & Vulnerability Management Program"],
    28: ["Vendor Onboarding Due Diligence Checklist", "Third-Party Security Assessment Questionnaire Process"],
    29: ["Third-Party Security Assessment Questionnaire Process", "Vendor Risk Management Program"],
    30: ["Vendor Onboarding Due Diligence Checklist"],
    31: ["Vendor Risk Management Program", "Disaster Recovery Runbooks & Failover Testing"],
    32: ["Third-Party Security Assessment Questionnaire Process"],
    33: ["Vendor Onboarding Due Diligence Checklist"],
    34: ["DOT Driver Qualification File Management Program"],
    35: ["Stakeholder & Legal/Regulatory Requirements Inventory", "Named Data Protection / Privacy Officer"],
    36: ["Stakeholder & Legal/Regulatory Requirements Inventory"],
    37: ["DOT Driver Qualification File Management Program"],
    38: ["OSHA Recordkeeping & EHS Management Program"],
    39: ["Vendor Onboarding Due Diligence Checklist"],
    40: ["Forklift & Warehouse Equipment Safety Program"],
    41: ["DOT Driver Qualification File Management Program"],
    42: ["MENA Executive Protection & Duty-of-Care Protocol"],
    43: ["Heat Illness Prevention Program"],
    44: ["Forklift & Warehouse Equipment Safety Program", "OSHA Recordkeeping & EHS Management Program"],
}


# ============================================================================
# Generation logic
# ============================================================================

IMPLEMENTATION_STATUSES = ["Not Implemented", "Planned", "Partially Implemented", "Largely Implemented", "Fully Implemented"]
IMPLEMENTATION_WEIGHTS = [0.06, 0.10, 0.24, 0.34, 0.26]

EFFECTIVENESS_BY_IMPLEMENTATION = {
    "Not Implemented": ["Ineffective"],
    "Planned": ["Ineffective", "Partially Effective"],
    "Partially Implemented": ["Partially Effective", "Largely Effective"],
    "Largely Implemented": ["Largely Effective", "Fully Effective"],
    "Fully Implemented": ["Largely Effective", "Fully Effective"],
}

FINDINGS_TEMPLATES = {
    "Ineffective": "Control is not operating; no evidence of consistent execution was observed during the assessment period.",
    "Partially Effective": "Control is operating but with notable gaps in consistency or coverage; partial evidence of execution observed.",
    "Largely Effective": "Control is operating as designed for the substantial majority of instances reviewed, with minor exceptions noted.",
    "Fully Effective": "Control is operating as designed; no exceptions identified during the assessment period.",
}


def random_date(start: date, end: date) -> str:
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, max(delta, 0)))).isoformat()


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def build_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA_PATH.read_text())

    # ---- CSF reference data ----
    csf = json.loads(CSF_REFERENCE_PATH.read_text())
    for fn in csf["functions"]:
        cur.execute(
            "INSERT INTO csf_functions (function_id, name, description, sort_order) VALUES (?,?,?,?)",
            (fn["function_id"], fn["name"], fn["description"], fn["sort_order"]),
        )
        for cat in fn["categories"]:
            cur.execute(
                "INSERT INTO csf_categories (category_id, function_id, name, description) VALUES (?,?,?,?)",
                (cat["category_id"], fn["function_id"], cat["name"], cat["description"]),
            )

    # ---- Business units ----
    for name, location, desc in BUSINESS_UNITS:
        cur.execute(
            "INSERT INTO business_units (name, location, description) VALUES (?,?,?)",
            (name, location, desc),
        )
    bu_id = {name: i + 1 for i, name in enumerate(BU_NAMES)}

    # ---- Assets ----
    for name, atype, bu_idx, crit, desc in ASSETS:
        cur.execute(
            "INSERT INTO assets (name, asset_type, business_unit_id, criticality, description) VALUES (?,?,?,?,?)",
            (name, atype, bu_idx + 1, crit, desc),
        )
    asset_id = {name: i + 1 for i, name in enumerate(ASSET_NAMES)}

    # ---- Controls ----
    control_id = {}
    for i, (name, desc, ctype, cat_id, owner) in enumerate(CONTROLS):
        impl_status = weighted_choice(IMPLEMENTATION_STATUSES, IMPLEMENTATION_WEIGHTS)
        assessed_date = random_date(date(2025, 9, 1), TODAY)
        code = f"CTRL-{i + 1:04d}"
        cur.execute(
            """INSERT INTO controls
               (control_code, name, description, control_type, category_id, control_owner,
                implementation_status, last_assessed_date)
               VALUES (?,?,?,?,?,?,?,?)""",
            (code, name, desc, ctype, cat_id, owner, impl_status, assessed_date),
        )
        cid = cur.lastrowid
        control_id[name] = cid

        # One or two assessments per control
        n_assessments = 1 if impl_status in ("Not Implemented", "Planned") else random.choice([1, 1, 2])
        for a in range(n_assessments):
            eff = weighted_choice(
                EFFECTIVENESS_BY_IMPLEMENTATION[impl_status],
                [0.5, 0.5] if len(EFFECTIVENESS_BY_IMPLEMENTATION[impl_status]) == 2 else [1.0],
            )
            a_date = random_date(date(2025, 6, 1), TODAY) if a == 0 else random_date(date(2024, 6, 1), date(2025, 6, 1))
            cur.execute(
                """INSERT INTO assessments (control_id, assessment_date, assessor, effectiveness_rating, findings)
                   VALUES (?,?,?,?,?)""",
                (cid, a_date, random.choice(ASSESSORS), eff, FINDINGS_TEMPLATES[eff]),
            )

    # ---- Risks ----
    risk_id = {}
    inherent_records = []
    for i, (title, desc, category, asset_name, bu_name, owner) in enumerate(RISKS):
        # Inherent scoring: physical/safety/MENA-related risks skew higher impact;
        # cyber risks skew higher likelihood. This is a modeling assumption, stated
        # in the methodology tab, not a claim about any real organization.
        if category in ("Physical Security", "Safety / EHS") or "Riyadh" in (asset_name or ""):
            likelihood = random.randint(2, 4)
            impact = random.randint(3, 5)
        elif category == "Cybersecurity":
            likelihood = random.randint(3, 5)
            impact = random.randint(2, 5)
        else:
            likelihood = random.randint(2, 4)
            impact = random.randint(2, 4)
        inherent_score = likelihood * impact
        code = f"RISK-{i + 1:04d}"
        identified = random_date(date(2024, 1, 1), date(2025, 12, 1))
        status = weighted_choice(["Open", "Monitoring", "Closed"], [0.62, 0.28, 0.10])

        cur.execute(
            """INSERT INTO risks
               (risk_code, title, description, risk_category, asset_id, business_unit_id,
                date_identified, risk_owner, inherent_likelihood, inherent_impact,
                inherent_risk_score, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (code, title, desc, category,
             asset_id.get(asset_name) if asset_name else None,
             bu_id[bu_name], identified, owner, likelihood, impact, inherent_score, status),
        )
        rid = cur.lastrowid
        risk_id[title] = rid
        inherent_records.append((rid, title, category, likelihood, impact, inherent_score, status))

        # Map to controls
        mapped_controls = RISK_CONTROL_MAP.get(i, [])
        for cname in mapped_controls:
            cur.execute(
                "INSERT INTO risk_control_map (risk_id, control_id) VALUES (?,?)",
                (rid, control_id[cname]),
            )

    # ---- Residual risk assessments (analytical judgment layer) ----
    conn.commit()
    for rid, title, category, likelihood, impact, inherent_score, status in inherent_records:
        cur.execute(
            """SELECT c.implementation_status FROM risk_control_map rcm
               JOIN controls c ON c.control_id = rcm.control_id
               WHERE rcm.risk_id = ?""",
            (rid,),
        )
        statuses = [r[0] for r in cur.fetchall()]
        if not statuses:
            reduction_factor = 0.05
            rationale_evidence = "no mapped controls were identified for this risk in the current register"
        else:
            maturity_score = {
                "Not Implemented": 0.0, "Planned": 0.1, "Partially Implemented": 0.35,
                "Largely Implemented": 0.6, "Fully Implemented": 0.8,
            }
            avg_maturity = sum(maturity_score[s] for s in statuses) / len(statuses)
            reduction_factor = avg_maturity
            weakest = min(statuses, key=lambda s: maturity_score[s])
            rationale_evidence = (
                f"{len(statuses)} mapped control(s) reviewed; weakest observed implementation status is "
                f"'{weakest}' (see linked control assessments)"
            )

        residual_likelihood = max(1, round(likelihood * (1 - 0.5 * reduction_factor)))
        residual_impact = max(1, round(impact * (1 - 0.25 * reduction_factor)))
        residual_score = residual_likelihood * residual_impact

        rationale = (
            f"Inherent score {inherent_score} (L{likelihood} x I{impact}) adjusted for control coverage: "
            f"{rationale_evidence}. Impact is reduced conservatively relative to likelihood, reflecting that "
            f"control maturity more directly affects the probability of occurrence than the severity of "
            f"consequence if the risk materializes. Residual score: {residual_score} (L{residual_likelihood} x I{residual_impact})."
        )

        cur.execute(
            """INSERT INTO residual_risk_assessments
               (risk_id, assessment_date, analyst, residual_likelihood, residual_impact,
                residual_risk_score, rationale)
               VALUES (?,?,?,?,?,?,?)""",
            (rid, random_date(date(2025, 9, 1), TODAY), random.choice(ANALYSTS),
             residual_likelihood, residual_impact, residual_score, rationale),
        )

    # ---- Remediation actions ----
    action_templates = {
        "Cybersecurity": "Remediate identified gap through {ctrl_action}; validate via follow-up control assessment.",
        "Physical Security": "Implement physical security enhancement: {ctrl_action}.",
        "Operational": "Address operational gap via {ctrl_action}.",
        "Third-Party": "Complete vendor risk remediation: {ctrl_action}.",
        "Compliance / Regulatory": "Close compliance gap through {ctrl_action}.",
        "Safety / EHS": "Implement safety corrective action: {ctrl_action}.",
    }
    ctrl_actions = [
        "deploying/expanding the mapped control to full coverage",
        "formalizing and documenting the control procedure",
        "completing overdue control testing and remediating findings",
        "assigning a dedicated control owner and target completion date",
        "expanding monitoring coverage to close the identified gap",
    ]

    action_counter = 0
    for rid, title, category, likelihood, impact, inherent_score, status in inherent_records:
        if status == "Closed":
            continue
        cur.execute(
            """SELECT c.control_id, c.implementation_status FROM risk_control_map rcm
               JOIN controls c ON c.control_id = rcm.control_id
               WHERE rcm.risk_id = ? AND c.implementation_status IN
               ('Not Implemented','Planned','Partially Implemented')""",
            (rid,),
        )
        gaps = cur.fetchall()
        if not gaps and inherent_score < 15:
            continue  # no remediation needed: adequately controlled or low inherent risk

        n_actions = min(len(gaps), 2) if gaps else 1
        for a in range(max(n_actions, 1)):
            action_counter += 1
            control_ref = gaps[a][0] if a < len(gaps) else None
            priority = "Critical" if inherent_score >= 20 else "High" if inherent_score >= 12 else "Medium"
            target = random_date(TODAY, TODAY + timedelta(days=180))
            a_status = weighted_choice(["Not Started", "In Progress", "Completed", "Overdue"], [0.25, 0.40, 0.20, 0.15])
            closed = random_date(date(2025, 9, 1), TODAY) if a_status == "Completed" else None
            desc = action_templates[category].format(ctrl_action=random.choice(ctrl_actions))
            cur.execute(
                """INSERT INTO remediation_actions
                   (action_code, risk_id, control_id, description, owner, priority, target_date, status, date_closed)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (f"REM-{action_counter:04d}", rid, control_ref, desc,
                 random.choice(OWNERS), priority, target, a_status, closed),
            )

    conn.commit()
    conn.close()
    print(f"Database built: {DB_PATH}")

    # Summary stats
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for table in ["business_units", "assets", "risks", "controls", "risk_control_map",
                  "assessments", "residual_risk_assessments", "remediation_actions"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n} rows")
    conn.close()


if __name__ == "__main__":
    build_database()
