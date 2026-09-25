"""
Canonical 29-Merchant Synthetic Master Dataset Generator for FraudLens AI.
Generates 20,000 realistic, time-sequenced synthetic transactions across 29 fictional merchants
with 55 columns encompassing Customer, Merchant, Device, Location, Time, Behavioral, and Security features.
Ensures zero data leakage and authentic synthetic fraud patterns.
"""

import os
import random
import datetime
import numpy as np
import pandas as pd

# Set deterministic seed for reproducibility
np.random.seed(42)
random.seed(42)

# Master Definition of the Exact 29 Fictional Merchants
MERCHANTS_MASTER = [
    {
        "merchant_id": "M001",
        "merchant_name": "NovaMart Fresh",
        "merchant_category": "Grocery & Supermarket",
        "merchant_subcategory": "Supermarket / Hypermarket",
        "merchant_city": "Chennai",
        "merchant_area": "T Nagar",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600017",
        "merchant_latitude": 13.0418,
        "merchant_longitude": 80.2341,
        "merchant_business_age_years": 8,
        "merchant_average_ticket": 1250.0,
        "merchant_operating_hours": "07:00-22:30",
        "merchant_payment_channels": "POS,UPI,CARD,ONLINE",
        "historical_fraud_pattern": "Card testing / micro-burst velocity",
        "base_fraud_rate": 0.012,
    },
    {
        "merchant_id": "M002",
        "merchant_name": "CircuitBay Electronics",
        "merchant_category": "Consumer Electronics",
        "merchant_subcategory": "Laptops & Gadgets",
        "merchant_city": "Chennai",
        "merchant_area": "Velachery",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600042",
        "merchant_latitude": 12.9759,
        "merchant_longitude": 80.2212,
        "merchant_business_age_years": 6,
        "merchant_average_ticket": 32000.0,
        "merchant_operating_hours": "10:00-21:30",
        "merchant_payment_channels": "POS,ONLINE,EMI,UPI",
        "historical_fraud_pattern": "Stolen payment details / high-ticket electronics delivery",
        "base_fraud_rate": 0.048,
    },
    {
        "merchant_id": "M003",
        "merchant_name": "Pulse Mobile Hub",
        "merchant_category": "Mobile Store",
        "merchant_subcategory": "Smartphones & Accessories",
        "merchant_city": "Chennai",
        "merchant_area": "Tambaram",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600045",
        "merchant_latitude": 12.9249,
        "merchant_longitude": 80.1278,
        "merchant_business_age_years": 4,
        "merchant_average_ticket": 18500.0,
        "merchant_operating_hours": "09:30-21:30",
        "merchant_payment_channels": "POS,UPI,CARD",
        "historical_fraud_pattern": "New device abuse / rapid checkout surge",
        "base_fraud_rate": 0.035,
    },
    {
        "merchant_id": "M004",
        "merchant_name": "Aurelia Gold House",
        "merchant_category": "Jewellery",
        "merchant_subcategory": "Gold & Diamond Jewellery",
        "merchant_city": "Coimbatore",
        "merchant_area": "RS Puram",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "641002",
        "merchant_latitude": 11.0089,
        "merchant_longitude": 76.9514,
        "merchant_business_age_years": 14,
        "merchant_average_ticket": 78000.0,
        "merchant_operating_hours": "10:00-20:30",
        "merchant_payment_channels": "POS,CARD,TRANSFER",
        "historical_fraud_pattern": "Account takeover / card-not-present luxury surge",
        "base_fraud_rate": 0.065,
    },
    {
        "merchant_id": "M005",
        "merchant_name": "UrbanThread Studio",
        "merchant_category": "Fashion / Apparel",
        "merchant_subcategory": "Designer & Ready-to-wear",
        "merchant_city": "Chennai",
        "merchant_area": "Anna Nagar",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600040",
        "merchant_latitude": 13.0850,
        "merchant_longitude": 80.2101,
        "merchant_business_age_years": 5,
        "merchant_average_ticket": 4800.0,
        "merchant_operating_hours": "10:30-22:00",
        "merchant_payment_channels": "POS,ONLINE,UPI,CARD",
        "historical_fraud_pattern": "Refund abuse / credential stuffing",
        "base_fraud_rate": 0.022,
    },
    {
        "merchant_id": "M006",
        "merchant_name": "MedicoCare Pharmacy",
        "merchant_category": "Pharmacy",
        "merchant_subcategory": "Medicines & Surgical Supplies",
        "merchant_city": "Madurai",
        "merchant_area": "KK Nagar",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "625020",
        "merchant_latitude": 9.9252,
        "merchant_longitude": 78.1498,
        "merchant_business_age_years": 10,
        "merchant_average_ticket": 1450.0,
        "merchant_operating_hours": "24_HOURS",
        "merchant_payment_channels": "POS,UPI,CARD,ONLINE",
        "historical_fraud_pattern": "Nighttime micro card testing",
        "base_fraud_rate": 0.015,
    },
    {
        "merchant_id": "M007",
        "merchant_name": "SpiceRoute Kitchen",
        "merchant_category": "Restaurant",
        "merchant_subcategory": "Fine Dining & Chettinad",
        "merchant_city": "Chennai",
        "merchant_area": "Adyar",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600020",
        "merchant_latitude": 13.0012,
        "merchant_longitude": 80.2565,
        "merchant_business_age_years": 7,
        "merchant_average_ticket": 2200.0,
        "merchant_operating_hours": "11:30-23:30",
        "merchant_payment_channels": "POS,UPI,CARD",
        "historical_fraud_pattern": "Cloned card POS terminal replay",
        "base_fraud_rate": 0.018,
    },
    {
        "merchant_id": "M008",
        "merchant_name": "BeanCircuit Cafe",
        "merchant_category": "Cafe",
        "merchant_subcategory": "Specialty Coffee & Bakery",
        "merchant_city": "Bengaluru",
        "merchant_area": "Indiranagar",
        "merchant_state": "Karnataka",
        "merchant_pincode": "560038",
        "merchant_latitude": 12.9784,
        "merchant_longitude": 77.6408,
        "merchant_business_age_years": 3,
        "merchant_average_ticket": 650.0,
        "merchant_operating_hours": "07:30-23:00",
        "merchant_payment_channels": "UPI,POS,CARD",
        "historical_fraud_pattern": "QR code spoofing / fast velocity dining",
        "base_fraud_rate": 0.009,
    },
    {
        "merchant_id": "M009",
        "merchant_name": "RapidFuel Station",
        "merchant_category": "Fuel Station",
        "merchant_subcategory": "Petrol, Diesel & EV Fast Charge",
        "merchant_city": "Salem",
        "merchant_area": "Fairlands",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "636016",
        "merchant_latitude": 11.6643,
        "merchant_longitude": 78.1460,
        "merchant_business_age_years": 9,
        "merchant_average_ticket": 3100.0,
        "merchant_operating_hours": "24_HOURS",
        "merchant_payment_channels": "POS,FLEET_CARD,UPI",
        "historical_fraud_pattern": "Automated fleet card skimming",
        "base_fraud_rate": 0.024,
    },
    {
        "merchant_id": "M010",
        "merchant_name": "HarborView Residency",
        "merchant_category": "Hotel / Hospitality",
        "merchant_subcategory": "Business & Luxury Hotel",
        "merchant_city": "Chennai",
        "merchant_area": "OMR",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600096",
        "merchant_latitude": 12.9165,
        "merchant_longitude": 80.2285,
        "merchant_business_age_years": 6,
        "merchant_average_ticket": 9500.0,
        "merchant_operating_hours": "24_HOURS",
        "merchant_payment_channels": "ONLINE,POS,CARD,TRANSFER",
        "historical_fraud_pattern": "Online travel booking fraud with stolen corporate credentials",
        "base_fraud_rate": 0.041,
    },
    {
        "merchant_id": "M011",
        "merchant_name": "SkyTrail Travels",
        "merchant_category": "Travel Agency",
        "merchant_subcategory": "Flight & International Tour Packages",
        "merchant_city": "Coimbatore",
        "merchant_area": "Gandhipuram",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "641012",
        "merchant_latitude": 11.0183,
        "merchant_longitude": 76.9664,
        "merchant_business_age_years": 11,
        "merchant_average_ticket": 44000.0,
        "merchant_operating_hours": "09:00-20:00",
        "merchant_payment_channels": "ONLINE,TRANSFER,CARD",
        "historical_fraud_pattern": "Mule-account ticket arbitrage & fast cancellation fraud",
        "base_fraud_rate": 0.052,
    },
    {
        "merchant_id": "M012",
        "merchant_name": "DashDine Delivery",
        "merchant_category": "Food Delivery",
        "merchant_subcategory": "Quick Commerce & Meal Delivery",
        "merchant_city": "Chennai",
        "merchant_area": "Sholinganallur",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600119",
        "merchant_latitude": 12.9010,
        "merchant_longitude": 80.2279,
        "merchant_business_age_years": 4,
        "merchant_average_ticket": 520.0,
        "merchant_operating_hours": "06:00-02:00",
        "merchant_payment_channels": "UPI,CARD,ONLINE,WALLET",
        "historical_fraud_pattern": "Promo code abuse / stolen wallet balances",
        "base_fraud_rate": 0.014,
    },
    {
        "merchant_id": "M013",
        "merchant_name": "CartNest Online",
        "merchant_category": "E-commerce",
        "merchant_subcategory": "Multi-category Marketplace",
        "merchant_city": "Chennai",
        "merchant_area": "Guindy",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600032",
        "merchant_latitude": 13.0067,
        "merchant_longitude": 80.2026,
        "merchant_business_age_years": 5,
        "merchant_average_ticket": 6200.0,
        "merchant_operating_hours": "24_HOURS",
        "merchant_payment_channels": "ONLINE,UPI,CARD,NETBANKING",
        "historical_fraud_pattern": "Account takeover + triangulation shipping fraud",
        "base_fraud_rate": 0.045,
    },
    {
        "merchant_id": "M014",
        "merchant_name": "OakLine Furnishings",
        "merchant_category": "Furniture",
        "merchant_subcategory": "Teak Wood & Modern Home Decor",
        "merchant_city": "Madurai",
        "merchant_area": "Bypass Road",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "625016",
        "merchant_latitude": 9.9320,
        "merchant_longitude": 78.1090,
        "merchant_business_age_years": 12,
        "merchant_average_ticket": 38000.0,
        "merchant_operating_hours": "10:00-21:00",
        "merchant_payment_channels": "POS,CARD,TRANSFER,EMI",
        "historical_fraud_pattern": "Invoice redirection fraud / fake payment slips",
        "base_fraud_rate": 0.029,
    },
    {
        "merchant_id": "M015",
        "merchant_name": "HomeSphere Appliances",
        "merchant_category": "Home Appliances",
        "merchant_subcategory": "Refrigerators, ACs & Kitchen Tech",
        "merchant_city": "Coimbatore",
        "merchant_area": "Saibaba Colony",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "641011",
        "merchant_latitude": 11.0315,
        "merchant_longitude": 76.9450,
        "merchant_business_age_years": 9,
        "merchant_average_ticket": 27500.0,
        "merchant_operating_hours": "09:30-21:00",
        "merchant_payment_channels": "POS,EMI,CARD,UPI",
        "historical_fraud_pattern": "Carding attacks with immediate in-store pickup",
        "base_fraud_rate": 0.038,
    },
    {
        "merchant_id": "M016",
        "merchant_name": "MotoCare Garage",
        "merchant_category": "Auto Service",
        "merchant_subcategory": "Car Service & Detailing Hub",
        "merchant_city": "Chennai",
        "merchant_area": "Pallikaranai",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600100",
        "merchant_latitude": 12.9372,
        "merchant_longitude": 80.2014,
        "merchant_business_age_years": 7,
        "merchant_average_ticket": 8900.0,
        "merchant_operating_hours": "08:30-20:30",
        "merchant_payment_channels": "POS,UPI,CARD",
        "historical_fraud_pattern": "Over-invoicing / synthetic card payments",
        "base_fraud_rate": 0.021,
    },
    {
        "merchant_id": "M017",
        "merchant_name": "AutoForge Parts",
        "merchant_category": "Spare Parts",
        "merchant_subcategory": "OEM Industrial & Auto Components",
        "merchant_city": "Hosur",
        "merchant_area": "Mookandapalli",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "635126",
        "merchant_latitude": 12.7409,
        "merchant_longitude": 77.8253,
        "merchant_business_age_years": 15,
        "merchant_average_ticket": 16500.0,
        "merchant_operating_hours": "09:00-19:30",
        "merchant_payment_channels": "TRANSFER,POS,CARD",
        "historical_fraud_pattern": "Business email compromise / fake beneficiary update",
        "base_fraud_rate": 0.033,
    },
    {
        "merchant_id": "M018",
        "merchant_name": "PageTurn Book House",
        "merchant_category": "Bookstore",
        "merchant_subcategory": "Academic, Fiction & Stationery",
        "merchant_city": "Trichy",
        "merchant_area": "Thillai Nagar",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "620018",
        "merchant_latitude": 10.8282,
        "merchant_longitude": 78.6854,
        "merchant_business_age_years": 16,
        "merchant_average_ticket": 850.0,
        "merchant_operating_hours": "09:00-21:30",
        "merchant_payment_channels": "POS,UPI,CARD,ONLINE",
        "historical_fraud_pattern": "Low-value card testing bots",
        "base_fraud_rate": 0.008,
    },
    {
        "merchant_id": "M019",
        "merchant_name": "ArenaSport World",
        "merchant_category": "Sports Retail",
        "merchant_subcategory": "Fitness Equipment & Sports Wear",
        "merchant_city": "Chennai",
        "merchant_area": "Nungambakkam",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600034",
        "merchant_latitude": 13.0604,
        "merchant_longitude": 80.2405,
        "merchant_business_age_years": 6,
        "merchant_average_ticket": 5600.0,
        "merchant_operating_hours": "10:00-21:30",
        "merchant_payment_channels": "POS,ONLINE,UPI,CARD",
        "historical_fraud_pattern": "Stolen card chargeback on premium sports gear",
        "base_fraud_rate": 0.026,
    },
    {
        "merchant_id": "M020",
        "merchant_name": "GameGrid Arena",
        "merchant_category": "Gaming",
        "merchant_subcategory": "Esports, Consoles & Virtual Credits",
        "merchant_city": "Bengaluru",
        "merchant_area": "Koramangala",
        "merchant_state": "Karnataka",
        "merchant_pincode": "560095",
        "merchant_latitude": 12.9352,
        "merchant_longitude": 77.6245,
        "merchant_business_age_years": 4,
        "merchant_average_ticket": 3400.0,
        "merchant_operating_hours": "10:00-01:00",
        "merchant_payment_channels": "ONLINE,UPI,CARD,WALLET",
        "historical_fraud_pattern": "Virtual item laundering & bot-driven micro transactions",
        "base_fraud_rate": 0.055,
    },
    {
        "merchant_id": "M021",
        "merchant_name": "GlowCraft Salon",
        "merchant_category": "Salon / Beauty",
        "merchant_subcategory": "Spa & Grooming Studio",
        "merchant_city": "Chennai",
        "merchant_area": "Porur",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600116",
        "merchant_latitude": 13.0382,
        "merchant_longitude": 80.1565,
        "merchant_business_age_years": 5,
        "merchant_average_ticket": 2800.0,
        "merchant_operating_hours": "09:00-21:00",
        "merchant_payment_channels": "POS,UPI,CARD",
        "historical_fraud_pattern": "Unusual late-night transaction spikes",
        "base_fraud_rate": 0.011,
    },
    {
        "merchant_id": "M022",
        "merchant_name": "SkillSpring Academy",
        "merchant_category": "Education / Training",
        "merchant_subcategory": "Professional Certifications & Tech Bootcamps",
        "merchant_city": "Chennai",
        "merchant_area": "Mylapore",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600004",
        "merchant_latitude": 13.0368,
        "merchant_longitude": 80.2676,
        "merchant_business_age_years": 8,
        "merchant_average_ticket": 22000.0,
        "merchant_operating_hours": "08:30-19:30",
        "merchant_payment_channels": "ONLINE,NETBANKING,CARD,UPI",
        "historical_fraud_pattern": "Stolen corporate card enrollments",
        "base_fraud_rate": 0.028,
    },
    {
        "merchant_id": "M023",
        "merchant_name": "SwiftBox Logistics",
        "merchant_category": "Courier / Logistics",
        "merchant_subcategory": "Express Parcel & Freight Delivery",
        "merchant_city": "Tiruppur",
        "merchant_area": "Avinashi Road",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "641603",
        "merchant_latitude": 11.1085,
        "merchant_longitude": 77.3411,
        "merchant_business_age_years": 9,
        "merchant_average_ticket": 4200.0,
        "merchant_operating_hours": "08:00-21:00",
        "merchant_payment_channels": "POS,UPI,CARD,ONLINE",
        "historical_fraud_pattern": "Interception fraud / address redirection",
        "base_fraud_rate": 0.020,
    },
    {
        "merchant_id": "M024",
        "merchant_name": "LinkWave Telecom",
        "merchant_category": "Telecom Retail",
        "merchant_subcategory": "Fiber Broadband & Postpaid Plans",
        "merchant_city": "Erode",
        "merchant_area": "Perundurai Road",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "638011",
        "merchant_latitude": 11.3410,
        "merchant_longitude": 77.7172,
        "merchant_business_age_years": 10,
        "merchant_average_ticket": 1950.0,
        "merchant_operating_hours": "09:30-20:30",
        "merchant_payment_channels": "UPI,CARD,ONLINE,POS",
        "historical_fraud_pattern": "SIM swap bill recharge surges",
        "base_fraud_rate": 0.017,
    },
    {
        "merchant_id": "M025",
        "merchant_name": "ShieldSure Services",
        "merchant_category": "Insurance Services",
        "merchant_subcategory": "General & Health Insurance Premium",
        "merchant_city": "Chennai",
        "merchant_area": "Egmore",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600008",
        "merchant_latitude": 13.0784,
        "merchant_longitude": 80.2607,
        "merchant_business_age_years": 13,
        "merchant_average_ticket": 14000.0,
        "merchant_operating_hours": "09:30-18:00",
        "merchant_payment_channels": "ONLINE,NETBANKING,CARD",
        "historical_fraud_pattern": "Premium diversion / fake policy payment slips",
        "base_fraud_rate": 0.019,
    },
    {
        "merchant_id": "M026",
        "merchant_name": "GreenLeaf Wellness",
        "merchant_category": "Health & Wellness",
        "merchant_subcategory": "Organic Nutrition & Ayurveda",
        "merchant_city": "Trichy",
        "merchant_area": "Srirangam",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "620006",
        "merchant_latitude": 10.8624,
        "merchant_longitude": 78.6947,
        "merchant_business_age_years": 6,
        "merchant_average_ticket": 2100.0,
        "merchant_operating_hours": "08:00-21:00",
        "merchant_payment_channels": "POS,UPI,ONLINE,CARD",
        "historical_fraud_pattern": "Subscription card stuffing",
        "base_fraud_rate": 0.013,
    },
    {
        "merchant_id": "M027",
        "merchant_name": "BrickHarbor Realty",
        "merchant_category": "Real Estate / Property Services",
        "merchant_subcategory": "Rental Escrow & Facility Management",
        "merchant_city": "Chennai",
        "merchant_area": "Porur",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "600116",
        "merchant_latitude": 13.0350,
        "merchant_longitude": 80.1600,
        "merchant_business_age_years": 11,
        "merchant_average_ticket": 65000.0,
        "merchant_operating_hours": "09:00-19:00",
        "merchant_payment_channels": "TRANSFER,NETBANKING,CARD",
        "historical_fraud_pattern": "Security deposit phishing / escrow hijacking",
        "base_fraud_rate": 0.039,
    },
    {
        "merchant_id": "M028",
        "merchant_name": "CraftCove Home Decor",
        "merchant_category": "Home Decor",
        "merchant_subcategory": "Handicrafts & Art Pieces",
        "merchant_city": "Thanjavur",
        "merchant_area": "Medical College Road",
        "merchant_state": "Tamil Nadu",
        "merchant_pincode": "613004",
        "merchant_latitude": 10.7684,
        "merchant_longitude": 79.1245,
        "merchant_business_age_years": 8,
        "merchant_average_ticket": 7400.0,
        "merchant_operating_hours": "09:30-20:30",
        "merchant_payment_channels": "POS,UPI,CARD,ONLINE",
        "historical_fraud_pattern": "Cross-border tourist chargebacks",
        "base_fraud_rate": 0.023,
    },
    {
        "merchant_id": "M029",
        "merchant_name": "CloudDesk Digital",
        "merchant_category": "Software / Digital Services",
        "merchant_subcategory": "Cloud Infrastructure & SaaS Tools",
        "merchant_city": "Bengaluru",
        "merchant_area": "Whitefield",
        "merchant_state": "Karnataka",
        "merchant_pincode": "560066",
        "merchant_latitude": 12.9698,
        "merchant_longitude": 77.7499,
        "merchant_business_age_years": 7,
        "merchant_average_ticket": 19800.0,
        "merchant_operating_hours": "24_HOURS",
        "merchant_payment_channels": "ONLINE,CARD,TRANSFER",
        "historical_fraud_pattern": "Cryptomining VM rental with stolen credit cards",
        "base_fraud_rate": 0.058,
    },
]

# Distinct Customer Behavioral Pools (500 synthetic customers)
CUSTOMERS = []
LOCATIONS = [
    "Chennai", "Coimbatore", "Madurai", "Salem", "Bengaluru",
    "Hosur", "Trichy", "Tiruppur", "Erode", "Thanjavur", "Kochi", "Hyderabad"
]

for i in range(1, 501):
    c_id = f"CUST-{1000 + i}"
    c_loc = random.choice(LOCATIONS)
    avg_amt = float(random.choice([800, 1500, 2800, 4500, 8500, 14000, 25000, 45000]))
    max_amt = float(avg_amt * random.uniform(2.5, 6.0))
    age_days = random.randint(15, 1200)
    CUSTOMERS.append({
        "customer_id": c_id,
        "usual_location": c_loc,
        "avg_amount": avg_amt,
        "max_amount": max_amt,
        "account_age_days": age_days,
        "device_id": f"DEV-{c_id[-4:]}-MAIN",
        "device_type": random.choice(["mobile_android", "mobile_ios", "desktop_windows", "web_browser"]),
    })


def generate_canonical_dataset(num_records: int = 20000, output_path: str = "data/raw/fraudlens_master_synthetic_transactions_29_merchants.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_date = datetime.datetime(2026, 1, 1, 0, 0, 0)
    records = []

    # Time progression simulation over 90 days
    current_time = start_date
    delta_minutes = (90 * 24 * 60) / num_records

    for idx in range(1, num_records + 1):
        tx_id = f"TXN-{100000 + idx}"
        
        # Advance timestamp slightly with small random jitter
        jitter = random.uniform(-2.0, 2.0)
        current_time += datetime.timedelta(minutes=max(delta_minutes + jitter, 0.5))
        tx_hour = current_time.hour
        tx_dow = current_time.weekday()
        is_weekend = 1 if tx_dow >= 5 else 0
        is_night = 1 if (tx_hour >= 23 or tx_hour <= 5) else 0

        # Choose Customer & Merchant
        cust = random.choice(CUSTOMERS)
        merchant = random.choice(MERCHANTS_MASTER)

        # Baseline probabilities
        is_merchant_online = "ONLINE" in merchant["merchant_payment_channels"]
        is_same_city = (cust["usual_location"] == merchant["merchant_city"])
        
        # Determine if this transaction will trigger a synthetic fraud scenario
        # Targeted realistic fraud rate ~ 4.2% across dataset
        fraud_trigger_prob = merchant["base_fraud_rate"] * (1.8 if is_night else 1.0)
        is_fraud_tx = 1 if random.random() < fraud_trigger_prob else 0

        # Behavioral & Security dynamics
        if is_fraud_tx:
            # Synthetic Fraud Dynamics
            scenario_choice = random.choice([
                ("Account takeover", "Pre-auth", "High-value off-hours takeover with sudden device change"),
                ("Stolen payment details", "Post-auth", "Card testing burst on luxury / digital merchant"),
                ("Card testing", "Pre-auth", "Rapid micro transactions from bot client"),
                ("New-device abuse", "Pre-auth", "New untrusted mobile client in non-home location"),
                ("Credential compromise", "Chargeback", "Repeated failed login attempts followed by high ticket purchase"),
                ("Mule-account behavior", "Post-auth", "Cross-city velocity anomaly and rapid transfer surge"),
            ])
            fraud_type, fraud_stage, fraud_scenario = scenario_choice

            amount = float(round(merchant["merchant_average_ticket"] * random.uniform(1.8, 4.5), 2))
            is_new_device = 1 if random.random() < 0.85 else 0
            is_trusted_device = 0 if is_new_device else (1 if random.random() < 0.3 else 0)
            dev_type = random.choice(["unknown_bot", "mobile_android", "desktop_windows"]) if is_new_device else cust["device_type"]
            dev_id = f"DEV-ROGUE-{random.randint(1000, 9999)}" if is_new_device else cust["device_id"]
            
            is_new_beneficiary = 1 if random.random() < 0.78 else 0
            beneficiary_name = f"BEN-{random.choice(['ApexGlobal', 'NovaCrypto', 'QuickRemit', 'SwiftTransfer'])}-{random.randint(100, 999)}"
            ben_id = f"BEN-{random.randint(1000, 9999)}"
            ben_prior_count = 0 if is_new_beneficiary else random.randint(1, 3)

            is_location_changed = 1 if random.random() < 0.75 else 0
            curr_location = random.choice(["Dubai", "Lagos", "Singapore", "Moscow", "London", "Nairobi"]) if is_location_changed and random.random() < 0.4 else random.choice(LOCATIONS)
            loc_distance = float(random.randint(250, 4500)) if is_location_changed else float(random.randint(1, 15))

            tx_last_1h = random.randint(3, 12)
            tx_last_24h = random.randint(8, 28)
            tx_last_7d = random.randint(15, 60)

            failed_tx_attempts = random.randint(1, 6)
            failed_login_attempts = random.randint(1, 5)
            recent_pw_change = 1 if random.random() < 0.45 else 0

        else:
            # Genuine Transaction Dynamics
            fraud_type = "None"
            fraud_stage = "Resolved Genuine"
            fraud_scenario = "Clean Baseline Transaction"

            amount = float(round(merchant["merchant_average_ticket"] * random.uniform(0.3, 1.4), 2))
            is_new_device = 1 if random.random() < 0.08 else 0
            is_trusted_device = 1 if not is_new_device else 0
            dev_type = cust["device_type"] if not is_new_device else random.choice(["mobile_android", "mobile_ios"])
            dev_id = cust["device_id"] if not is_new_device else f"DEV-NEW-{random.randint(1000, 9999)}"

            is_new_beneficiary = 1 if random.random() < 0.12 else 0
            beneficiary_name = merchant["merchant_name"]
            ben_id = f"BEN-M-{merchant['merchant_id']}"
            ben_prior_count = random.randint(2, 25) if not is_new_beneficiary else 0

            is_location_changed = 1 if (not is_same_city and random.random() < 0.15) else 0
            curr_location = cust["usual_location"] if not is_location_changed else merchant["merchant_city"]
            loc_distance = float(random.randint(1, 25)) if not is_location_changed else float(random.randint(30, 180))

            tx_last_1h = random.randint(0, 2)
            tx_last_24h = random.randint(1, 5)
            tx_last_7d = random.randint(3, 18)

            failed_tx_attempts = 0 if random.random() < 0.94 else 1
            failed_login_attempts = 0 if random.random() < 0.96 else 1
            recent_pw_change = 0 if random.random() < 0.98 else 1

        # Ratios & Deviations (Time-safe historical context)
        amount_to_avg_ratio = round(amount / max(cust["avg_amount"], 1.0), 3)
        amount_deviation_zscore = round((amount - cust["avg_amount"]) / max(cust["avg_amount"] * 0.4, 10.0), 3)

        tx_type = random.choice(merchant["merchant_payment_channels"].split(","))

        # 55 Exact Columns Record Assembly
        record = {
            # 1. Transaction Core
            "transaction_id": tx_id,
            "transaction_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": tx_type,
            "amount": amount,
            "currency": "INR",
            
            # 2. Merchant Profile
            "merchant_id": merchant["merchant_id"],
            "merchant_name": merchant["merchant_name"],
            "merchant_category": merchant["merchant_category"],
            "merchant_subcategory": merchant["merchant_subcategory"],
            "merchant_city": merchant["merchant_city"],
            "merchant_area": merchant["merchant_area"],
            "merchant_state": merchant["merchant_state"],
            "merchant_pincode": merchant["merchant_pincode"],
            "merchant_latitude": merchant["merchant_latitude"],
            "merchant_longitude": merchant["merchant_longitude"],
            "merchant_business_age_years": merchant["merchant_business_age_years"],
            "merchant_average_ticket": merchant["merchant_average_ticket"],
            "merchant_operating_hours": merchant["merchant_operating_hours"],
            "merchant_payment_channels": merchant["merchant_payment_channels"],
            
            # 3. Customer Context
            "customer_id": cust["customer_id"],
            "customer_account_age_days": cust["account_age_days"],
            "customer_usual_location": cust["usual_location"],
            "customer_historical_avg_amount": cust["avg_amount"],
            "customer_historical_max_amount": cust["max_amount"],
            "customer_total_transactions_prior": random.randint(5, 120),
            
            # 4. Device Context
            "device_id": dev_id,
            "device_type": dev_type,
            "is_new_device": is_new_device,
            "is_trusted_device": is_trusted_device,
            
            # 5. Beneficiary Context
            "beneficiary_id": ben_id,
            "beneficiary_name": beneficiary_name,
            "is_new_beneficiary": is_new_beneficiary,
            "beneficiary_prior_tx_count": ben_prior_count,
            
            # 6. Time & Velocity Context
            "transaction_hour": tx_hour,
            "day_of_week": tx_dow,
            "is_weekend": is_weekend,
            "is_night_transaction": is_night,
            "transactions_last_1h": tx_last_1h,
            "transactions_last_24h": tx_last_24h,
            "transactions_last_7d": tx_last_7d,
            
            # 7. Behavioral Deviation Context
            "amount_to_avg_ratio": amount_to_avg_ratio,
            "amount_deviation_zscore": amount_deviation_zscore,
            
            # 8. Location Context
            "current_location": curr_location,
            "is_location_changed": is_location_changed,
            "location_distance_km": loc_distance,
            
            # 9. Security Signals
            "failed_transaction_attempts_24h": failed_tx_attempts,
            "failed_login_attempts_24h": failed_login_attempts,
            "recent_password_change": recent_pw_change,
            
            # 10. Historical Synthetic Merchant Fraud Context
            "merchant_historical_fraud_rate": round(merchant["base_fraud_rate"] * 100, 2),
            "merchant_historical_fraud_count": random.randint(4, 45),
            "merchant_historical_fraud_pattern": merchant["historical_fraud_pattern"],
            
            # 11. Target & Investigation Context
            "is_fraud": is_fraud_tx,
            "fraud_type": fraud_type,
            "fraud_stage": fraud_stage,
            "fraud_scenario": fraud_scenario,
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records with {len(df.columns)} columns to {output_path}")
    print(f"Total Unique Merchants: {df['merchant_id'].nunique()}")
    print(f"Fraud Class Distribution:\n{df['is_fraud'].value_counts(normalize=True)}")
    return df


if __name__ == "__main__":
    generate_canonical_dataset()
