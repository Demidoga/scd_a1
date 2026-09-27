"""Seed complaint data — realistic municipal complaints in Urdu-influenced
English, spread across every category. docs/architecture/database.md §4.

Kept as plain data (text, location, reporter_contact) separate from app/seed.py's
runner logic so the two can be reviewed/extended independently.
"""

SEED_COMPLAINTS: list[tuple[str, str, str | None]] = [
    # --- water ---
    (
        "Water supply line burst near our house since fajr, water flowing "
        "on the road and wasting, kindly send someone urgently.",
        "Street 12, G-9/1, Islamabad",
        "0301-2345678",
    ),
    (
        "No water coming in our tap from three days, whole mohalla is "
        "suffering, we have to buy tanker water which is very costly for us.",
        "Gulshan-e-Iqbal Block 5, Karachi",
        None,
    ),
    (
        "Sir the water pipeline is leaking outside house number 45 from "
        "last week, water is getting wasted daily, please fix it.",
        "Model Town Block C, Lahore",
        "0333-1122334",
    ),
    (
        "Water tanker line is contaminated, smell is very bad and water is "
        "not clean for drinking, children are getting sick because of this.",
        "Sector 15-A/4, Korangi, Karachi",
        None,
    ),
    (
        "Main supply pipe near masjid chowk is broken since two days, "
        "low pressure water only coming for 1 hour, kindly resolve.",
        "Chowk Yadgar, Peshawar",
        "0345-9988776",
    ),
    (
        "Paani ki line mein crack hai near the park, water is entering the "
        "sewerage line and mixing, this is health hazard for whole area.",
        "Satellite Town Phase 2, Rawalpindi",
        None,
    ),
    # --- electricity ---
    (
        "Power cut since yesterday evening, transformer is making sound "
        "and sparking, very dangerous for children playing nearby, please send lineman.",
        "Johar Town Block J-2, Lahore",
        "0312-4455667",
    ),
    (
        "Bijli ka meter box is open and wires are hanging loose outside "
        "house, risk of shock, we have small kids at home, please fix urgently.",
        "North Nazimabad Block L, Karachi",
        None,
    ),
    (
        "Voltage fluctuation is destroying our appliances daily, fridge "
        "and fan both burned this month, kindly check the transformer.",
        "Sector F-10 Markaz, Islamabad",
        "0300-1234567",
    ),
    (
        "Streetside electric pole wire is touching the tree branches, "
        "during rain it is sparking very much, someone will get hurt.",
        "Township Block A, Lahore",
        None,
    ),
    (
        "No electricity for the whole colony since morning, control room "
        "is not picking phone, we are suffering in this heat with no fan.",
        "Landhi Colony No. 3, Karachi",
        "0321-7654321",
    ),
    (
        "Transformer near the school is overloaded and burning smell is "
        "coming, teachers have complained, kindly inspect before school opens.",
        "Cantt Bazar, Rawalpindi",
        None,
    ),
    # --- sanitation ---
    (
        "Sewerage line is overflow from last two days, dirty water is "
        "entering the street and smell is unbearable, mosquitoes increasing.",
        "Liaquatabad Block 10, Karachi",
        "0303-2233445",
    ),
    (
        "Garbage is not collected from our street for one full week, "
        "kachra is piling up and stray dogs are spreading it everywhere.",
        "Allama Iqbal Town, Lahore",
        None,
    ),
    (
        "Nala beside our house is blocked with plastic waste, whenever it "
        "rains the water comes inside houses, kindly clean urgently before monsoon.",
        "Ferozepur Road, Lahore",
        "0334-5566778",
    ),
    (
        "Drain cover is broken near the bus stop, open gutter is very "
        "dangerous especially for children going to school, please cover it.",
        "Saddar Bazar, Rawalpindi",
        None,
    ),
    (
        "Waste from the nearby market is being dumped on our street corner "
        "daily, whole area is smelling very bad, this is not acceptable.",
        "Anarkali Bazar, Lahore",
        None,
    ),
    (
        "Sewage water is mixing with the water supply line in our lane, "
        "we are scared to drink the water, this is very serious matter kindly check.",
        "Orangi Town Sector 5, Karachi",
        "0345-1112223",
    ),
    # --- roads ---
    (
        "Big pothole in the middle of the road since many months, two "
        "motorcycle accidents already happened at night, please repair soon.",
        "University Road, Peshawar",
        None,
    ),
    (
        "Road is completely damaged after the rain, footpath also broken, "
        "old people are finding it very hard to walk, kindly resurface.",
        "Mall Road, Rawalpindi",
        "0300-9876543",
    ),
    (
        "Speed breaker is not visible at night, no paint or sign board, "
        "already one accident happened, please mark it properly for safety.",
        "Shahrah-e-Faisal, Karachi",
        None,
    ),
    (
        "Sadak par bohat saray gaddy (potholes) hain, rickshaw wale bhi "
        "pareshan hain, monsoon ke baad se koi repair nahi hua, kindly fix.",
        "Multan Road, Lahore",
        "0321-3344556",
    ),
    (
        "Footpath tiles are all broken and uneven near the market, elderly "
        "citizens keep falling, this footpath needs urgent repair work.",
        "Bank Road, Rawalpindi",
        None,
    ),
    (
        "Road near the roundabout has deep cracks and standing water after "
        "every rain, traffic jam happens daily because of this, please resolve.",
        "Airport Road, Quetta",
        None,
    ),
    # --- streetlights ---
    (
        "Streetlight is not working since one month on our whole street, "
        "it is very dark at night and not safe for women coming home from work.",
        "Defence Phase 6, Karachi",
        "0333-6677889",
    ),
    (
        "Street light pole is leaning dangerously after the storm, it "
        "might fall on the road anytime, kindly send team to fix or remove it.",
        "Bahria Town Sector C, Lahore",
        None,
    ),
    (
        "Three lamp posts in a row are not working near the park, kids "
        "play there till evening and it becomes unsafe after dark, please repair.",
        "F-8 Markaz, Islamabad",
        None,
    ),
    (
        "Streetlight wiring is exposed and hanging low from the pole, very "
        "dangerous during rain, kindly send electrician before someone gets hurt.",
        "G.T. Road, Gujranwala",
        "0345-2233114",
    ),
    (
        "Light pole near the masjid has been flickering and buzzing for "
        "weeks, sounds like it could short circuit, please inspect soon.",
        "Samanabad, Lahore",
        None,
    ),
    (
        "No street light at all on our lane since construction of new "
        "houses, very dark and unsafe path especially for school children.",
        "Hayatabad Phase 3, Peshawar",
        "0312-8899001",
    ),
    # --- other ---
    (
        "Stray dogs have increased very much in our area, they chase "
        "children going to school, kindly arrange for their vaccination or removal.",
        "Wapda Town, Lahore",
        None,
    ),
    (
        "Public park equipment is all broken and rusted, swings are "
        "dangerous for children now, kindly repair or replace before someone gets hurt.",
        "Shalimar Park, Karachi",
        "0300-4455223",
    ),
    (
        "Illegal encroachment on the main road by shopkeepers is causing "
        "daily traffic jam, kindly take action against this encroachment.",
        "Raja Bazar, Rawalpindi",
        None,
    ),
    (
        "Noise pollution from the wedding hall goes on till 2am daily "
        "during this season, whole colony cannot sleep, please take notice.",
        "Cavalry Ground, Lahore",
        "0321-5566990",
    ),
    (
        "Boundary wall of the government school has collapsed after rain, "
        "children's safety is at risk, kindly repair before school reopens.",
        "Nazimabad Block 2, Karachi",
        None,
    ),
    (
        "Public toilet near the bus terminal is in very bad condition, no "
        "water and doors broken, kindly clean and repair for public use.",
        "Faisal Chowk, Peshawar",
        None,
    ),
]
