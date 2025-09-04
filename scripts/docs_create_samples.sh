#!/bin/bash
# Path: scripts/create_sample_docs.sh
# File: create_sample_docs.sh  
# Execute from: /Users/hugodiaz/Astoria/hf_spaces/astoria_open
# Purpose: Create sample maritime documents for vector database testing

echo "🏗️ Creating sample maritime documents..."

# Create sample documents
cat > data/maritime_history/vessel_types_guide.txt << 'EOF'
# Maritime Vessel Types and Classifications

## Brigs
A brig is a type of sailing vessel defined by having two square-rigged masts. Brigs were widely used in the 18th and 19th centuries for both military and commercial purposes. The term "brig" is short for "brigantine," though true brigantines have different rigging configurations.

Historical brigs like the ELL (built in 1272) represent some of the earliest examples of this vessel type. These ships typically ranged from 75 to 165 feet in length and could carry substantial cargo loads.

## Schooners  
Schooners are sailing vessels characterized by fore-and-aft rigged sails on two or more masts. They were particularly popular in American waters and were known for their speed and maneuverability.

The schooner design evolved significantly from the 17th century onward, with vessels like those built in the 1800s representing the height of schooner design and construction techniques.

## Historical Significance
Maritime vessels from different eras reflect the technological and cultural developments of their times. Medieval ships like those from the 13th century demonstrate early shipbuilding techniques, while 19th-century vessels show the transition toward modern maritime technology.
EOF

cat > data/maritime_history/ship_construction_history.txt << 'EOF'
# Historical Ship Construction Techniques

## Medieval Shipbuilding (13th Century)
Ships built in the medieval period, such as vessels from 1272, used traditional clinker-built construction methods. These techniques involved overlapping wooden planks secured with iron rivets.

Medieval shipwrights relied on oak timber for hull construction, as it provided excellent durability and resistance to marine borers. The construction process was largely based on traditional knowledge passed down through generations.

## 17th Century Developments  
By the 1600s, shipbuilding had evolved to include more sophisticated design principles. Vessels like the CLARABELL (1666) incorporated improved hull designs that enhanced both cargo capacity and seaworthiness.

The 17th century saw the introduction of better tools and measurement techniques, leading to more standardized construction practices across different shipyards.

## 19th Century Innovation
The 1800s marked a revolutionary period in ship construction. Steam power began supplementing sail power, and iron components started replacing traditional wooden elements in critical structural areas.

Ships built during this era, such as those from 1820, represented a transition period between traditional sailing vessels and the emerging age of steam-powered maritime transport.

## Construction Materials and Methods
Traditional shipbuilding materials included various types of timber, iron fasteners, hemp rope, and canvas sails. The selection of materials was crucial for vessel longevity and performance in marine environments.
EOF

cat > data/maritime_history/maritime_safety_regulations.txt << 'EOF'
# Maritime Safety Standards and Regulations

## Historical Context
Maritime safety regulations have evolved significantly over centuries. Early regulations focused primarily on basic seaworthiness requirements and cargo handling procedures.

## Vessel Registration and Documentation
Ship registration systems developed to track vessel ownership, construction details, and operational history. Registration numbers became mandatory for commercial vessels to ensure proper identification and regulatory compliance.

## Inspection Requirements
Regular vessel inspections became standard practice to ensure continued seaworthiness. These inspections cover hull integrity, rigging condition, and safety equipment availability.

Historical vessels often underwent periodic inspections to maintain their operational status and compliance with maritime regulations of their era.

## Tonnage Calculations
Gross tonnage measurements provide standardized methods for determining vessel size and capacity. These calculations affect regulatory requirements, port fees, and operational classifications.

## Flag State Responsibilities
Vessels operating under specific national flags must comply with that nation's maritime regulations and safety standards. Flag state jurisdiction determines applicable regulatory frameworks for international maritime operations.

## Current Status Classifications
Maritime authorities maintain records of vessel operational status, including active service, historical preservation, or decommissioned status. These classifications affect regulatory requirements and operational permissions.
EOF

cat > data/maritime_history/propulsion_systems.txt << 'EOF'
# Maritime Propulsion Systems Through History

## Wind Power Era
For centuries, maritime vessels relied exclusively on wind power for propulsion. Sail configurations varied significantly based on vessel type, intended use, and regional preferences.

Different sail arrangements, such as square-rigged or fore-and-aft configurations, offered various advantages in different wind conditions and operational requirements.

## Early Mechanical Propulsion
The introduction of steam engines revolutionized maritime transportation. Early steam-powered vessels often retained sail rigging as backup propulsion, creating hybrid propulsion systems.

Engine types varied from simple steam engines to more complex compound engines, each offering different power outputs and fuel efficiency characteristics.

## Horsepower Ratings
Maritime engines are rated by horsepower output, which determines vessel speed and cargo-carrying capacity. Historical records show the evolution from low-horsepower early engines to more powerful modern systems.

## Fuel Systems and Capacity
Fuel capacity became a critical design consideration with the introduction of mechanical propulsion. Vessels required sufficient fuel storage for extended voyages while maintaining cargo space efficiency.

Different fuel types, including coal, oil, and later diesel, each presented unique storage and handling requirements that influenced vessel design and operation.

## Maximum Speed Capabilities
Vessel speed capabilities depend on hull design, propulsion system power, and loading conditions. Historical vessels typically operated at lower speeds compared to modern maritime transport.

Speed requirements varied based on vessel purpose, from fast passenger services to slower but more efficient cargo transportation.
EOF

cat > data/maritime_history/maritime_dimensions_specifications.txt << 'EOF'
# Vessel Dimensions and Specifications

## Length Classifications
Maritime vessels are classified by overall length, which affects regulatory requirements, port accessibility, and operational capabilities. Historical vessels show significant variation in length based on intended purpose and construction era.

Vessel length measurements must account for various configurations, including bowsprit extensions and stern modifications that affect overall operational dimensions.

## Beam Measurements
Beam width determines vessel stability and cargo capacity. Wider beams generally provide greater stability but may limit access to certain ports or waterways with width restrictions.

Historical beam measurements reflect design priorities of different eras, with some periods favoring narrower designs for speed and others preferring wider configurations for stability.

## Draft Considerations
Vessel draft affects port accessibility and shallow water navigation capabilities. Deep-draft vessels can carry more cargo but are restricted to deeper ports and waterways.

Draft measurements are critical for navigation safety and operational planning, particularly in areas with varying water depths or tidal conditions.

## Tonnage Systems
Gross tonnage provides standardized vessel size measurements for regulatory and commercial purposes. These calculations consider internal volume rather than actual weight.

Historical tonnage calculations may vary from modern standards, requiring careful interpretation when comparing vessels from different eras.

## Structural Specifications
Vessel construction specifications include materials, structural methods, and design standards that affect operational capabilities and regulatory compliance.

Traditional construction methods used different materials and techniques compared to modern shipbuilding, resulting in vessels with unique structural characteristics and operational requirements.
EOF

echo "✅ Created 5 sample maritime documents in data/maritime_history/"
echo ""
echo "📁 Files created:"
ls -la data/maritime_history/
echo ""
echo "🚀 Next step: Run the ingestion script to load into vector database"
echo "   python scripts/pg_vector_manual_ingest.py"

#end-of-script