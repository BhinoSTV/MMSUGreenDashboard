#!/usr/bin/env python3
"""Build the MMSU SDG 15 (Life on Land) evidence documents for the THE Sustainability
Impact Ratings 2027 cycle, styled after MMSU's 2025 SDG 15 evidence report.

Usage:  python3 build.py            (sources with web addresses)
        python3 build.py --no-urls  (source titles only, for THE upload)
Output: html/*.html and pdf/*.pdf next to this script.

Photos live in assets/. A photo listed below whose file is missing renders as a labelled
placeholder frame; drop the image into assets/ under that filename and rebuild.
Facts here come only from the sources cited with each story (see checklist.md for
items still to be confirmed before submission).
"""
import base64
import html
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(HERE, "assets")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
# --no-urls: print source titles without web addresses (THE rejects link-heavy evidence).
NO_URLS = "--no-urls" in sys.argv

COMMITMENT = ("Take an active role in protecting and promoting sustainable use of "
              "terrestrial ecosystems, responsible land use, and biodiversity conservation.")
EVIDENCE_YEAR = "Evidence year: 2025 (calendar year)"

# ---------------------------------------------------------------- photos
# name -> caption. Files that exist in assets/ are embedded; others become placeholders.
PHOTOS = {
    "forest_reserve_planting_2025.jpg": "CAFSD graduands planting native trees and bamboo in the University Forest Reserves, Payao and Mabaleng, City of Batac, 2 July 2025.",
    "mangrove_seminar_2025.jpg": "Seminar-workshop on mangrove propagation and management for coastal municipalities, Center for Flexible Learning, 27–28 October 2025.",
    "pinili_bamboo_2025.jpg": "Bamboo propagation, nursery and plantation management training and bambusetum establishment, Barangay Aglipay, Pinili, 2025.",
    "alukon_training_2025.jpg": "Training on alukon (himbabao) propagation for farmers, Barangay 11 Sta. Rosa, Sarrat, 2 May 2025.",
    "pasuquin_mangrove_2025.jpg": "Mangrove planting and tripartite agreement signing at the National Greening Program site, Barangay Davila, Pasuquin, 2025.",
    "ifp_foodscape.jpg": "Partners receive indigenous food plant planting materials for the Community Foodscapes and Seedbanks, World Food Day 2025.",
    "pcaarrd_mangrove_site_badoc.jpg": "Project site in Badoc, Ilocos Norte. (Image credit: TTPD, DOST-PCAARRD)",
    "pcaarrd_launch_gonzales.jpg": "Project Leader Dr. Arlene L. Gonzales presents the project at its launch, MMSU Review Center, 27 June 2024. (Image credit: TTPD, DOST-PCAARRD)",
    "pcaarrd_launch_group.jpg": "The MMSU project team with DOST-PCAARRD, DENR-PENRO Ilocos Norte, the Provincial Government of Ilocos Norte and the LGUs of Badoc and Currimao at the launch. (Image credit: TTPD, DOST-PCAARRD)",
    "denr_dialogue_speaker.jpg": "Dr. Arlene L. Gonzales at the MMSU–DENR Region 1 dialogue on mangrove conservation, ILAARRDEC.",
    "denr_dialogue_meeting.jpg": "MMSU and DENR Region 1 officials during the dialogue at ILAARRDEC.",
    "idbd_poster.jpg": "Contest poster with the animal-photography ethical guidelines (deadline 30 May 2025).",
    "idbd_awarding.jpg": "Winner Chris Jeremiah C. Antonio receives his certificate from Dr. Arlene L. Gonzales, Chief of Sustainability and Futures Thinking.",
    "idbd_dove.jpg": "Photograph featured with the contest results.",
    "idbd_dragonfly.jpg": "Photograph featured with the contest results.",
    "soa_regenerative_2025.jpg": "MMSU School-on-the-Air season on regenerative vegetable farming, launched 24–25 June 2025.",
    "presidents_farm_field_day_2025.jpg": "President’s Farm Field Day: A Technology Showcase, in front of CAFSD, 28 October 2025.",
    "sirmata2040_plan.jpg": "Sirmata 2040 land use map of the MMSU campuses and reserve areas.",
}

# Where a missing photo can be obtained (shown on the placeholder).
PHOTO_SOURCE = {
    "forest_reserve_planting_2025.jpg": "MMSU News, 4 Jul 2025 (article 2468) or MMSU Public Affairs / CAFSD files",
    "mangrove_seminar_2025.jpg": "MMSU News, 5 Nov 2025 (article 2670) or the NbS mangrove project team",
    "pinili_bamboo_2025.jpg": "MMSU News, 3 Sep 2025, or the Extension Directorate",
    "alukon_training_2025.jpg": "MMSU News, 9 May 2025, or the Research Directorate",
    "pasuquin_mangrove_2025.jpg": "MMSU College of Industrial Technology files (third-party news photos need TMP Foundation permission)",
    "soa_regenerative_2025.jpg": "MMSU News, 26 Jun 2025, or the Extension Directorate",
    "presidents_farm_field_day_2025.jpg": "MMSU News article 2665 (4 Nov 2025), or the Extension Directorate",
    "sirmata2040_plan.jpg": "Sirmata 2040 LUDIP document (Office of Planning and Strategic Foresight)",
}

# ---------------------------------------------------------------- sources
SRC = {
    "forest2025": ("MMSU News, “CAFSD graduands plant trees, bamboos in Batac forest reserves,” 4 July 2025",
                   "https://www.mmsu.edu.ph/article/news/2468/cafsd-graduands-plant-trees-bamboos-in-batac-forest-reserves"),
    "salinged2024": ("MMSU News, “BS Forestry seniors leave green footprints with pre-graduation tree planting,” 11 July 2024",
                     "https://www.mmsu.edu.ph/article/news/2065/bs-forestry-seniors-leave-green-footprints-with-pre-graduation-tree-planting"),
    "station": ("MMSU Research Directorate, Station Profile",
                "https://research.mmsu.edu.ph/about/station-profile"),
    "mangroveseminar": ("MMSU News, “MMSU trains Ilocos Norte coastal towns on mangrove propagation and management,” 5 November 2025",
                        "https://www.mmsu.edu.ph/article/news/2670/mmsu-trains-ilocos-norte-coastal-towns-on-mangrove-propagation-and-management"),
    "pinili": ("MMSU News, “Sustainable livelihood: MMSU, ILAARRDEC hold bamboo training in Pinili,” 3 September 2025",
               "https://www.mmsu.edu.ph/news/sustainable-livelihood-mmsu-ilaarrdec-hold-bamboo-training-in-pinili"),
    "alukon": ("MMSU News, “MMSU trains Sarrat farmers on alukon propagation,” 9 May 2025",
               "https://www.mmsu.edu.ph/news/mmsu-trains-sarrat-farmers-on-alukon-propagation"),
    "ifp_seedbank": ("MMSU Extension Directorate, “MMSU expands indigenous food plant seedbanks and foodscapes in LGUs,” October 2025",
                     "https://extension.mmsu.edu.ph/news/show/389/mmsu-expands-indigenous-food-plant-seedbanks-and-foodscapes-in-lgus"),
    "ifp_award": ("MMSU Research Directorate, “MMSU research on indigenous food plants wins best paper at SUC-ACAP 2025 conference”",
                  "https://research.mmsu.edu.ph/news/details/mmsu-research-on-indigenous-food-plants-wins-best-paper-at-suc-acap-2025-conference"),
    "pcaarrd": ("DOST-PCAARRD, “DOST-PCAARRD, MMSU launch nature-based solutions project on mangrove management in Ilocos Norte,” 7 August 2024",
                "https://www.pcaarrd.dost.gov.ph/index.php/quick-information-dispatch-qid-articles/dost-pcaarrd-mmsu-launch-nature-based-solutions-project-on-mangrove-management-in-ilocos-norte"),
    "report2025": ("MMSU SDG 15 Life on Land report (2025), Office of Sustainability and Futures Thinking", None),
    "pasuquin": ("The Manila Times, “TMP Foundation adopts mangrove forest for climate mitigation,” 10 December 2025",
                 "https://www.manilatimes.net/2025/12/10/tmt-newswire/tmp-foundation-adopts-mangrove-forest-for-climate-mitigation/2239598"),
    "soa": ("MMSU News, “MMSU draws 1K enrollees for SOA program on sustainable vegetable farming,” 26 June 2025",
            "https://www.mmsu.edu.ph/news/mmsu-draws-1k-enrollees-for-soa-program-on-sustainable-vegetable-farming"),
    "fieldday": ("MMSU News, “MMSU President’s Farm showcases 8 rice varieties,” 4 November 2025",
                 "https://www.mmsu.edu.ph/article/news/2665/mmsu-presidents-farm-showcases-8-rice-varieties"),
    "sirmata": ("MMSU News, “CHED TWG OKs MMSU Sirmata 2040”",
                "https://www.mmsu.edu.ph/news/ched-twg-oks-mmsu-sirmata-2040"),
    "ludip_fund": ("MMSU News, “MMSU gets Php 2 M for LUDIP project”",
                   "https://www.mmsu.edu.ph/news/mmsu-gets-php-2-m-for-ludip-project"),
    "rec": ("MMSU News, “MMSU commits to ecological solid waste management in Region I,” 2 July 2025",
            "https://www.mmsu.edu.ph/news/mmsu-commits-to-ecological-solid-waste-management-in-region-i"),
}

# ---------------------------------------------------------------- stories
# Each story: title, photos (list), paragraphs (list), sources (keys).
S = {}

S["forest_planting"] = dict(
    title="CAFSD Graduands Plant Native Trees and Bamboo in the University Forest Reserves",
    photos=["forest_reserve_planting_2025.jpg"],
    paras=[
        "Some 230 graduating students of the College of Agriculture, Food and Sustainable Development (CAFSD) of Mariano Marcos State University (MMSU) planted trees and bamboo in the University Forest Reserves in Barangays Payao and Mabaleng, City of Batac, on July 2, 2025. The activity was led by CAFSD OIC-Dean Charlie Batin and the 2025 CAFSD Graduating Class Student Council, with Dr. Joselito Rosario, Director for Agribusiness, and Mr. Bonne Jovie Orteza of the MMSU Bamboo Research and Development Center.",
        "The graduands planted 120 seedlings of guijo and yakal, native dipterocarp timber species raised at the MMSU Central Nursery, in the Payao Forest Reserve, and 130 propagules of kawayan tinik, machiku and giant bamboo from the MMSU Bamboo Nursery in Mabaleng. The planting continues CAFSD’s pre-graduation tree-planting tradition, held in July 2024 by the BS Forestry graduates at Salinged Park, the university’s ecological park, and repeated by the CAFSD Class of 2026 at the Payao Forest Reserve in June 2026.",
    ],
    sources=["forest2025", "salinged2024"],
)

S["forest_reserve"] = dict(
    title="Enriching MMSU’s 1,068-Hectare Forest Reserves with Native Species",
    photos=["forest_reserve_planting_2025.jpg"],
    paras=[
        "MMSU manages Forest Reserve Areas in Barangays Lubbot and Payao, City of Batac, covering a total of 1,068.13 hectares, where the university’s forestry and agroforestry research is set up. The university maintains and extends these ecosystems with planting stock raised in its own nurseries, the MMSU Central Nursery and the MMSU Bamboo Nursery.",
        "On July 2, 2025, 230 CAFSD graduating students enriched the reserves with 120 seedlings of the native dipterocarps guijo and yakal in Payao and 130 propagules of kawayan tinik, machiku and giant bamboo in Mabaleng. The activity was led by CAFSD OIC-Dean Charlie Batin with the MMSU Bamboo Research and Development Center.",
    ],
    sources=["station", "forest2025"],
)

S["ifp_conservation"] = dict(
    title="Conserving Ilocos Indigenous Food Plants In Situ, Ex Situ and Circa Situ",
    photos=["ifp_foodscape.jpg"],
    paras=[
        "Through its Indigenous Food Plants (IFP) Program, MMSU conserves the wild and neglected food plants of Ilocos Norte, 46 of which were documented by the program in seven towns of the province. The program follows a triad of conservation approaches: an IFP Botanical Garden for ex situ conservation, a himbabao (alukon) genebank at the MMSU Forest Reserve, circa situ cultivation of wild yams, and the integration of IFPs into community foodscapes.",
        "In October 2025, in celebration of World Food Day, the MMSU Extension and Research Directorates established the second batch of Community Foodscapes and Seedbanks for Indigenous Food Plants with local government units and schools, at Eladio V. Barangan Memorial Elementary School in San Nicolas, Ilocos Norte. The foodscape sites serve as seedbanks and learning gardens, and partner communities receive planting materials and technical assistance to cultivate kapaskapas, alokon, pako, dalayap, wild singkamas and roselle.",
        "The IFP Program was adopted by the Regional Development Council of Region 1 as its first research and development initiative, and a study on the program by Dr. Menisa A. Antonio and co-authors won Best Paper in the Sustainable and Smart Agri-Aquaculture and Climate Resilience category of the SUC-ACAP 2025 Biennial Conference, held August 27–29, 2025, in Tagbilaran City, Bohol.",
    ],
    sources=["ifp_award", "ifp_seedbank", "report2025"],
)

S["mangrove_nbs"] = dict(
    title="Nature-based Solutions to Restore Mangrove Ecosystems in Badoc and Currimao",
    photos=["pcaarrd_mangrove_site_badoc.jpg", "pcaarrd_launch_gonzales.jpg"],
    paras=[
        "MMSU leads the DOST-PCAARRD-funded project “Nature-based Solutions (NbS) for Sustainable Mangrove Management and Resilient Coastal Communities Through Innovative Green Engineering Approach,” implemented from May 1, 2024 to April 30, 2026 under Project Leader Dr. Arlene L. Gonzales. Launched on June 27, 2024 at the MMSU Review Center, the project works in Badoc and Currimao, Ilocos Norte, with DENR-PENRO Ilocos Norte, the Provincial Government of Ilocos Norte, the LGUs of Badoc and Currimao, and local communities.",
        "The project addresses the poor hydrological conditions that keep young mangrove propagules from surviving, using technology-assisted plantations and locally available, ecologically friendly materials, including bamboo-engineered structures that protect young mangroves and improve their survival. In 2025 MMSU and DENR Region 1 met at ILAARRDEC to advance the work; DENR officials pledged technical support and active participation in restoration, monitoring and evaluation, building on a memorandum of understanding signed in October 2024.",
    ],
    sources=["pcaarrd", "report2025"],
)

S["idbd_contest"] = dict(
    title="2025 International Day for Biological Diversity Wildlife Photo Contest",
    photos=["idbd_poster.jpg", "idbd_awarding.jpg"],
    paras=[
        "MMSU, through its Office of Sustainability and Futures Thinking, marked the 2025 International Day for Biological Diversity with a Wildlife Photo Contest that invited the university community to document local wildlife and promote awareness of biodiversity conservation. Entrants followed animal-photography ethical guidelines: avoiding flash and loud noises, never using bait or food lures, following local laws and warning signs, keeping clear of nesting sites and sensitive habitats, and captioning photographs honestly. Entries were received until May 30, 2025.",
        "Chris Jeremiah C. Antonio, a third-year BA Communication student, was named winner and received a ₱1,000 gift voucher and a certificate from Dr. Arlene L. Gonzales, Chief of Sustainability and Futures Thinking.",
    ],
    sources=["report2025"],
)

S["mangrove_seminar"] = dict(
    title="MMSU Trains Coastal Towns on Mangrove Propagation, Management and Conservation",
    photos=["mangrove_seminar_2025.jpg"],
    paras=[
        "MMSU conducted a two-day Seminar-Workshop on Mangrove Propagation on October 27–28, 2025 at its Center for Flexible Learning for representatives of the coastal municipalities of Currimao, Pasuquin, Badoc and Burgos, Ilocos Norte, with officials of DENR-PENRO in attendance. The training was organized under the DOST-PCAARRD-funded nature-based solutions mangrove project led by Dr. Arlene Gonzales.",
        "Sessions covered the importance of mangrove ecosystems, nature-based solutions for conservation, legal frameworks for mangrove protection, and the roles of the academe and local government units in community-based mangrove management. Participants were also trained in nursery management and advanced propagation techniques for Avicennia and Sonneratia species and other local mangrove varieties.",
    ],
    sources=["mangroveseminar"],
)

S["alukon"] = dict(
    title="Farmers in Sarrat Trained to Propagate the Indigenous Alukon",
    photos=["alukon_training_2025.jpg"],
    paras=[
        "On May 2, 2025, the MMSU Research and Extension Directorates trained 64 farmers in Barangay 11 Sta. Rosa, Sarrat, Ilocos Norte, on the propagation of alukon (himbabao), a Philippine indigenous vegetable tree. Barangay officials, members of the Task Force Dagger Special Operations Foundation and representatives of the local government unit also attended. The training was held in response to requests from the community.",
        "Resource speakers Dr. Menisa Antonio, Engr. Josefa Pugat and Mr. Jayson Rasay of the Research Directorate presented recommended propagation strategies to establish sustained alukon production in the community and broaden the use of the crop for food and other applications.",
    ],
    sources=["alukon"],
)

S["ifp_learning"] = dict(
    title="Community Foodscapes as Learning Gardens for Indigenous Plants",
    photos=["ifp_foodscape.jpg"],
    paras=[
        "In October 2025, in celebration of World Food Day, the MMSU Extension and Research Directorates established the second batch of Community Foodscapes and Seedbanks for Indigenous Food Plants at Eladio V. Barangan Memorial Elementary School, San Nicolas, Ilocos Norte. Barangay officials of San Roque and Parut, Vintar, agricultural extension workers, school leaders and community representatives took part.",
        "The foodscape sites serve as seedbanks and learning gardens that encourage knowledge sharing and sustainable farming practices. Communities receive planting materials and technical assistance to cultivate indigenous crops such as kapaskapas, alokon, pako, dalayap, wild singkamas and roselle, conserving indigenous food resources across Ilocos Norte.",
    ],
    sources=["ifp_seedbank", "report2025"],
)

S["pinili"] = dict(
    title="Bamboo Propagation and Plantation Management Training in Pinili",
    photos=["pinili_bamboo_2025.jpg"],
    paras=[
        "The MMSU Extension Directorate and the College of Agriculture, Food and Sustainable Development, in partnership with Barangay Aglipay, Pinili, Ilocos Norte, and with the support of the Ilocos Agriculture, Aquatic and Natural Resources Research and Development Consortium (ILAARRDEC), conducted a two-day training on bamboo production in 2025.",
        "The training equipped 46 farmers, local leaders and community members with practical skills in bamboo propagation, nursery establishment and plantation management. Lectures covered the prospects of the bamboo industry and MMSU’s propagation methods, and participants helped establish a new bambusetum, a collection of bamboo species, in Barangay Aglipay.",
    ],
    sources=["pinili"],
)

S["pinili_short"] = dict(
    title="A New Bambusetum in Barangay Aglipay, Pinili",
    photos=["pinili_bamboo_2025.jpg"],
    paras=[
        "During a two-day bamboo production training in 2025, the MMSU Extension Directorate and CAFSD, with Barangay Aglipay, Pinili, and the support of ILAARRDEC, worked with 46 farmers, local leaders and community members to establish a new bambusetum, a collection of bamboo species, in Barangay Aglipay. The training covered bamboo propagation, nursery establishment and plantation management.",
    ],
    sources=["pinili"],
)

S["pasuquin"] = dict(
    title="MMSU, Pasuquin LGU and TMP Foundation Join to Restore a Mangrove Forest",
    photos=["pasuquin_mangrove_2025.jpg"],
    paras=[
        "In late 2025, Mariano Marcos State University entered into a tripartite agreement with the Municipal Government of Pasuquin, Ilocos Norte, and the Toyota Motor Philippines (TMP) Foundation for the conservation of a degraded two-hectare mangrove forest, a National Greening Program site in Barangay Davila, Pasuquin.",
        "The agreement was signed at the close of a planting activity in which about 110 volunteers, including members of the MMSU College of Industrial Technology, DENR-CENRO Bangui, the Municipal Environment and Natural Resources Office and residents of Barangay Davila, planted 1,750 mangrove seedlings. Over two years, the partners will plant 3,500 seedlings of the native mangrove species lapis-lapis and arinaya to strengthen the community’s natural defense against climate-related impacts and enhance biodiversity.",
    ],
    sources=["pasuquin"],
)

S["denr_partnership"] = dict(
    title="MMSU and DENR Region 1 Strengthen Partnership for Mangrove Conservation",
    photos=["denr_dialogue_speaker.jpg", "denr_dialogue_meeting.jpg"],
    paras=[
        "MMSU, in partnership with the Department of Environment and Natural Resources (DENR) Region 1, convened a dialogue at ILAARRDEC to advance mangrove conservation and coastal resilience in the Ilocos Region through science-based and community-centered approaches. Central to the dialogue was the DOST-PCAARRD-funded nature-based solutions mangrove project led by Dr. Arlene Gonzales.",
        "DENR officials pledged technical support and active participation in restoration, monitoring and evaluation activities, solidifying the partnership formalized through a memorandum of understanding signed in October 2024. The same project brought representatives of Currimao, Pasuquin, Badoc and Burgos, with DENR-PENRO, to MMSU’s mangrove propagation seminar-workshop on October 27–28, 2025.",
    ],
    sources=["report2025", "mangroveseminar"],
)

S["ifp_partners"] = dict(
    title="Indigenous Food Plant Foodscapes Established with Vintar and San Nicolas Partners",
    photos=["ifp_foodscape.jpg"],
    paras=[
        "In October 2025, the MMSU Extension and Research Directorates partnered with local government units and schools to establish Community Foodscapes and Seedbanks for Indigenous Food Plants. Held at Eladio V. Barangan Memorial Elementary School in San Nicolas, Ilocos Norte, the activity brought together officials of Barangays San Roque and Parut, Vintar, the Municipal Agriculture Office of Vintar, agricultural extension workers, school leaders and community representatives as the second batch of partner sites.",
        "The partner communities maintain the foodscapes as shared seedbanks and learning gardens, with planting materials and technical assistance from MMSU, to conserve indigenous food resources such as kapaskapas, alokon, pako, dalayap, wild singkamas and roselle.",
    ],
    sources=["ifp_seedbank", "report2025"],
)

S["rec"] = dict(
    title="MMSU Commits to the DENR-EMB Region I Regional Ecology Center",
    photos=[],
    paras=[
        "On July 1, 2025, in Bauang, La Union, MMSU signed a memorandum of commitment with the DENR–Environmental Management Bureau Region I and other government agencies, private sector representatives, non-government organizations and academic institutions for the Regional Ecology Center. MMSU was represented by Vice President for Planning and Strategic Foresight Mee Jay Domingo and Campus Sustainability Chief Ronnel Pagurayan.",
        "Under the commitment, MMSU supports improved solid waste management under Republic Act 9003 (Ecological Solid Waste Management Act) and Republic Act 11898 (Extended Producer Responsibility Act) through education and public information campaigns and the development of informational materials.",
    ],
    sources=["rec"],
)

S["soa"] = dict(
    title="School-on-the-Air Brings Regenerative Vegetable Farming to 1,000 Ilocanos",
    photos=["soa_regenerative_2025.jpg"],
    paras=[
        "A new season of the MMSU School-on-the-Air (SOA), the university’s radio-based educational program, opened on June 24 and 25, 2025 with 1,000 enrollees from the 22 municipalities and cities of Ilocos Norte. The season focused on regenerative vegetable farming for enhanced and sustainable production, with lessons on climate-smart practices and off-season vegetable seeding.",
        "Vegetable growers, rural improvement club members, agricultural extension workers and students followed the lessons, broadcast from June to December 2025 over DWFB Radyo Pilipinas Laoag, DWCI Radyo Adjo Piddig and DWNI Radyo Karruba Burgos. MMSU ran the program with the Provincial Government of Ilocos Norte, the Office of the Provincial Agriculturist, local government units, the Ilocos Agriculture, Aquatic and Natural Resources Research and Development Consortium, and the High-Value Crops Division of Ilocos Norte.",
    ],
    sources=["soa"],
)

S["fieldday"] = dict(
    title="President’s Farm Field Day Showcases Climate-Resilient Rice Varieties",
    photos=["presidents_farm_field_day_2025.jpg"],
    paras=[
        "On October 28, 2025, the MMSU Extension Directorate, with the Philippine Rice Research Institute (PhilRice) Batac Branch, held the President’s Farm Field Day: A Technology Showcase in front of the College of Agriculture, Food and Sustainable Development. Farmers and farmer-leaders, agricultural technicians from Ilocos Norte local government units, BS Agriculture students, and MMSU and PhilRice rice specialists viewed eight rice varieties grown under wet-season conditions.",
        "The varieties included four newly released by PhilRice, two public hybrids, and two suited to saline and rainfed conditions, among them NSIC Rc 686 (Salinas 39) and NSIC Rc 650 (Sahod Ulan 36), giving farmers options for saline-affected and rainfed fields. Speakers included MMSU President Dr. Virgilio Julius P. Manzano Jr., Extension Director Dr. Marlowe Aquino, and former MMSU President and PhilRice Executive Director Dr. Santiago R. Obien.",
    ],
    sources=["fieldday"],
)

S["sirmata"] = dict(
    title="Sirmata 2040: Planning MMSU’s Campuses and Reserve Lands for Two Decades",
    photos=["sirmata2040_plan.jpg"],
    paras=[
        "Sirmata 2040, MMSU’s Land Use Development and Infrastructure Plan (LUDIP), is the university’s 20-year guide for managing its land resources and infrastructure. Prepared under Republic Act 11396, which requires state universities and colleges to have a LUDIP, and supported by a Php 2 million grant from the Commission on Higher Education (CHED), the plan covers the future land use of the MMSU campuses and the university’s reserve areas in Nagbacsan, Payao, Lubbot and Sarnap, City of Batac, including the forest reserves where MMSU’s forestry and agroforestry research is set up.",
        "The plan was developed through stakeholder consultations, sectoral studies and campus planning workshops, and was endorsed by the CHED Technical Working Group after validation visits to the campuses.",
    ],
    sources=["sirmata", "ludip_fund", "station"],
)

# ---------------------------------------------------------------- documents
DOCS = [
    dict(code="15.2.1", file="SDG15_15.2.1_Events_on_sustainable_land_use",
         title="Events about sustainable use of land",
         question="Support or organise events aimed to promote conservation and sustainable utilisation of the land, including forests and wild land.",
         stories=["forest_planting", "fieldday", "idbd_contest"]),
    dict(code="15.2.3", file="SDG15_15.2.3_Maintain_and_extend_biodiversity",
         title="Maintain and extend current ecosystems’ biodiversity",
         question="Work directly to maintain and extend existing ecosystems and their biodiversity, of both plants and animals, especially ecosystems under threat.",
         stories=["forest_reserve", "ifp_conservation", "pinili_short", "mangrove_nbs"]),
    dict(code="15.2.4", file="SDG15_15.2.4_Educational_programmes_on_ecosystems",
         title="Educational programmes on ecosystems",
         question="Offer educational programmes on ecosystems (looking at wild flora and fauna) for local or national communities.",
         stories=["mangrove_seminar", "alukon", "ifp_learning"]),
    dict(code="15.2.5", file="SDG15_15.2.5_Sustainable_land_management_for_agriculture",
         title="Sustainable management of land for agriculture (educational outreach)",
         question="Offer educational programme/outreach for local or national communities on sustainable management of land for agriculture.",
         stories=["soa", "pinili", "fieldday", "alukon"]),
    dict(code="15.3.3", file="SDG15_15.3.3_Local_biodiversity_in_planning",
         title="Local biodiversity included in planning and development",
         question="Include local biodiversity into any planning and development process (e.g. construction of new buildings).",
         stories=["sirmata"]),
    dict(code="15.3.5", file="SDG15_15.3.5_Collaboration_for_shared_land_ecosystems",
         title="Collaboration for shared land ecosystems",
         question="Collaborate with the local community to maintain shared land ecosystems.",
         stories=["pasuquin", "denr_partnership", "ifp_partners", "pinili_short"]),
]
SUPPORTING = dict(code="15.4", title="Land-sensitive waste disposal (supporting context)",
                  question="Not a policy document; recorded as supporting context for 15.4.2.",
                  stories=["rec"])

# ---------------------------------------------------------------- rendering
def font_css():
    """Reuse the self-hosted Montserrat and Work Sans faces from the dashboard."""
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    faces = []
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", src, re.S):
        if re.search(r"'(Montserrat|Work Sans)'", m.group(1)):
            faces.append("@font-face{" + m.group(1) + "}")
    return "\n".join(faces)


def img_uri(name):
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        return None
    mime = "image/png" if name.endswith(".png") else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def esc(t):
    return html.escape(t, quote=True)


def photo_html(names):
    if not names:
        return ""
    cells = []
    for n in names:
        uri = img_uri(n)
        cap = esc(PHOTOS.get(n, ""))
        if uri:
            cells.append(f'<figure class="ph"><div class="frame"><img src="{uri}" alt="{cap}"></div>'
                         f'<figcaption>{cap}</figcaption></figure>')
        else:
            where = esc(PHOTO_SOURCE.get(n, "MMSU Public Affairs files"))
            cells.append(f'<figure class="ph"><div class="frame missing"><div>'
                         f'<b>PHOTO TO INSERT</b><span>{cap}</span>'
                         f'<span class="fn">assets/{esc(n)}</span><span class="fn">Source: {where}</span>'
                         f'</div></div><figcaption>{cap}</figcaption></figure>')
    cls = "photos one" if len(cells) == 1 else "photos"
    return f'<div class="{cls}">' + "".join(cells) + "</div>"


def sources_html(keys):
    items = []
    for k in keys:
        label, url = SRC[k]
        items.append(f"<li>{esc(label)}" + (f'<br><span class="url">{esc(url)}</span>' if url and not NO_URLS else "") + "</li>")
    return '<div class="src"><b>Source</b><ul>' + "".join(items) + "</ul></div>"


def story_html(key):
    s = S[key]
    paras = "".join(f"<p>{esc(p)}</p>" for p in s["paras"])
    return (f'<section class="story"><div class="shead"><h2>{esc(s["title"])}</h2>{photo_html(s["photos"])}</div>'
            f'{paras}{sources_html(s["sources"])}</section>')


SDG_TILE = """<div class="tile"><div class="tnum">15</div><div class="tlab">LIFE<br>ON LAND</div>
<svg viewBox="0 0 100 70" class="tree" aria-hidden="true">
<circle cx="42" cy="22" r="13" fill="#fff"/><circle cx="56" cy="26" r="12" fill="#fff"/><circle cx="34" cy="32" r="11" fill="#fff"/>
<circle cx="50" cy="36" r="12" fill="#fff"/><rect x="45" y="40" width="6" height="18" fill="#fff"/>
<path d="M66 16 q5 -4 10 0 q5 -4 10 0" stroke="#fff" stroke-width="3" fill="none"/>
<path d="M70 30 q5 -4 10 0 q5 -4 10 0" stroke="#fff" stroke-width="3" fill="none"/>
<rect x="10" y="60" width="80" height="3.5" fill="#fff"/><rect x="10" y="66" width="80" height="3.5" fill="#fff"/></svg></div>"""

CSS = """
@page { size: Letter; margin: 0.65in 0.7in 0.75in;
  @top-left { content: ""; border-bottom: 5px solid #0b4a16; vertical-align: bottom; margin-bottom: 0.18in; }
  @top-center { content: ""; border-bottom: 5px solid #0b4a16; vertical-align: bottom; margin-bottom: 0.18in; }
  @top-right { content: ""; border-bottom: 5px solid #0b4a16; vertical-align: bottom; margin-bottom: 0.18in; }
  @bottom-left { content: "Mariano Marcos State University · City of Batac, Ilocos Norte"; font-family: 'Montserrat', sans-serif; font-size: 7.5pt; color: #5b5b57; border-top: 5px solid #0b4a16; vertical-align: top; padding-top: 6px; margin-top: 0.15in; }
  @bottom-right { content: "THE Sustainability Impact Ratings 2027 · SDG 15 · p. " counter(page); font-family: 'Montserrat', sans-serif; font-size: 7.5pt; color: #5b5b57; border-top: 5px solid #0b4a16; vertical-align: top; padding-top: 6px; margin-top: 0.15in; }
}
:root { --g:#3faa3a; --gd:#0b4a16; --gl:#56c02b; --ink:#1d1d1b; --mut:#5b5b57; }
* { box-sizing: border-box; }
html,body { margin:0; background:#fff; color:var(--ink); font-family:'Work Sans',sans-serif; font-size:10.6pt; line-height:1.55; }
header.top { display:flex; gap:22px; align-items:flex-start; margin-bottom:14px; }
.tile { flex:0 0 1.45in; height:1.45in; background:var(--gl); color:#fff; position:relative; padding:9px 10px; }
.tnum { font-family:'Montserrat',sans-serif; font-weight:800; font-size:34pt; line-height:1; letter-spacing:-1px; }
.tlab { position:absolute; left:58px; top:13px; font-family:'Montserrat',sans-serif; font-weight:700; font-size:10pt; line-height:1.1; }
.tree { position:absolute; left:14px; right:14px; bottom:8px; width:calc(100% - 28px); }
.commit h3 { margin:0 0 6px; font-family:'Montserrat',sans-serif; font-weight:800; color:var(--g); text-decoration:underline; text-underline-offset:4px; font-size:14pt; }
.commit p { margin:0; font-family:'Montserrat',sans-serif; font-weight:700; font-style:italic; font-size:13pt; line-height:1.35; }
.meta { border-left:5px solid var(--gl); background:#f1f8ee; padding:9px 12px; margin:6px 0 16px; font-size:9.5pt; }
.meta .code { font-family:'Montserrat',sans-serif; font-weight:800; color:var(--gd); font-size:11pt; }
.meta .q { color:var(--mut); font-style:italic; }
.story { margin:0 0 22px; break-inside:auto; }
.shead { break-inside:avoid; break-after:avoid; }
.story h2 { font-family:'Montserrat',sans-serif; font-weight:800; color:var(--g); text-align:center; font-size:17pt; line-height:1.22; margin:14px 0 14px; break-after:avoid; }
.photos { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:0 0 12px; break-inside:avoid; }
.photos.one { grid-template-columns:1fr; width:78%; margin-left:auto; margin-right:auto; }
.ph { margin:0; }
.frame { border:5px solid var(--g); border-radius:34px; overflow:hidden; height:2.45in; background:#e9f3e5; }
.photos.one .frame { height:2.65in; }
.frame img { width:100%; height:100%; object-fit:cover; display:block; }
.frame.missing { border-style:dashed; display:flex; align-items:center; justify-content:center; text-align:center; padding:14px; }
.frame.missing b { display:block; font-family:'Montserrat',sans-serif; color:var(--gd); letter-spacing:.08em; margin-bottom:6px; }
.frame.missing span { display:block; font-size:8.6pt; color:var(--mut); }
.frame.missing .fn { font-family:monospace; font-size:7.6pt; margin-top:5px; }
figcaption { font-size:7.8pt; color:var(--mut); font-style:italic; margin-top:4px; line-height:1.35; text-align:center; }
p { text-align:justify; margin:0 0 9px; orphans:3; widows:3; }
.src { font-size:7.8pt; color:var(--mut); border-top:1px solid #d5e6cf; padding-top:5px; margin-top:6px; break-inside:avoid; break-before:avoid; }
.src ul { margin:2px 0 0; padding-left:14px; } .src .url { word-break:break-all; color:#2c6e2a; }
.cover { height:8.9in; display:flex; flex-direction:column; justify-content:center; break-after:page; }
.cover .tile { flex:none; width:1.45in; }
.cover .big { font-family:'Montserrat',sans-serif; font-weight:800; font-size:30pt; color:var(--gd); line-height:1.1; margin:22px 0 10px; }
.cover .sub { font-family:'Montserrat',sans-serif; font-weight:600; font-size:13pt; color:var(--g); }
.cover .note { margin-top:30px; font-size:9.5pt; color:var(--mut); max-width:6in; }
table.idx { width:100%; border-collapse:collapse; font-size:9pt; margin:10px 0 18px; }
table.idx th, table.idx td { border-bottom:1px solid #d5e6cf; padding:6px 6px; text-align:left; vertical-align:top; }
table.idx th { font-family:'Montserrat',sans-serif; color:var(--gd); }
.secthead { break-before:page; }
"""


def page_shell(title, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title>
<style>{font_css()}{CSS}</style></head><body>
{body}</body></html>"""


def header_html(doc):
    return (f'<header class="top">{SDG_TILE}<div class="commit"><h3>MMSU’s Commitment</h3><p>{esc(COMMITMENT)}</p></div></header>'
            f'<div class="meta"><div class="code">SDG {esc(doc["code"])} · {esc(doc["title"])}</div>'
            f'<div class="q">{esc(doc["question"])}</div><div>{EVIDENCE_YEAR}</div></div>')


def build_doc(doc):
    body = header_html(doc) + "".join(story_html(k) for k in doc["stories"])
    return page_shell(f'MMSU SDG {doc["code"]}', body)


def build_compendium():
    rows = "".join(
        f'<tr><td><b>{esc(d["code"])}</b></td><td>{esc(d["title"])}</td><td>'
        + "<br>".join(esc(S[k]["title"]) for k in d["stories"]) + "</td></tr>"
        for d in DOCS + [SUPPORTING])
    cover = (f'<div class="cover">{SDG_TILE}<div class="big">SDG 15 Life on Land<br>Evidence Compendium 2025</div>'
             f'<div class="sub">Mariano Marcos State University · THE Sustainability Impact Ratings 2027</div>'
             f'<div class="note">Compiled from MMSU, DOST-PCAARRD and news sources for the 2027 data submission '
             f'(due 9 November 2026). Each section corresponds to one THE SDG 15 indicator. Evidence year: 2025.</div></div>')
    index = f'<h2 style="font-family:Montserrat;color:#0b4a16;">Contents by indicator</h2><table class="idx"><tr><th>Indicator</th><th>Question</th><th>Evidence</th></tr>{rows}</table>'
    sections = ""
    for d in DOCS + [SUPPORTING]:
        sections += f'<div class="secthead">{header_html(d)}</div>' + "".join(story_html(k) for k in d["stories"])
    return page_shell("MMSU SDG 15 Evidence Compendium 2025", cover + index + sections)


def render_pdf(html_path, pdf_path):
    cmd = [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={pdf_path}", "file://" + html_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def export_json():
    import json
    from PIL import Image
    dims = {n: Image.open(os.path.join(ASSETS, n)).size for n in PHOTOS if os.path.exists(os.path.join(ASSETS, n))}
    data = dict(dims=dims, commitment=COMMITMENT, evidence_year=EVIDENCE_YEAR, docs=DOCS, supporting=SUPPORTING,
                stories=S, photos=PHOTOS, photo_source=PHOTO_SOURCE,
                sources={k: {"label": v[0], "url": v[1]} for k, v in SRC.items()})
    json.dump(data, open(os.path.join(HERE, "content.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    export_json()
    os.makedirs(os.path.join(HERE, "html"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "pdf"), exist_ok=True)
    jobs = [(d["file"], build_doc(d)) for d in DOCS]
    jobs.append(("SDG15_Evidence_Compendium_2025", build_compendium()))
    for name, page in jobs:
        hp = os.path.join(HERE, "html", name + ".html")
        open(hp, "w", encoding="utf-8").write(page)
        if "--html-only" not in sys.argv:
            render_pdf(hp, os.path.join(HERE, "pdf", name + ".pdf"))
        print("built", name)
    missing = sorted({p for d in DOCS for k in d["stories"] for p in S[k]["photos"]
                      if not os.path.exists(os.path.join(ASSETS, p))})
    if missing:
        print("photos still to add:", ", ".join(missing))


if __name__ == "__main__":
    main()
