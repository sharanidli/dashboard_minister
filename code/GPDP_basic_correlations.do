/*-------------------------------------------------------------------------------
* TITLE             : GPDP Admin data - Match complete data with UGP

* COMPONENT         : [1] Cleaning raw dataset

* AUTHOR            : Ankita

* DATE              : 16.06.2026

* DESCRIPTION       : 
	
* INPUT DATASET     : "${db}/3_Analyse/Input/2024_scraping/gpdp/eswarajv5_20.06.25.dta"

* OUTPUT DATASET    : 

* SUMMARY FINDINGS  : 

*------------------------------------------------------------------------------*/

*-------------------------------------------------------------------------------*
**#				[1] Preliminary Cleaning
*-------------------------------------------------------------------------------*
/*
import excel "C:\Users\ankita\Dropbox\Peer Effects and Role Models\Analysis_Experiment\3_Analyse\Input\Administrative Data\GPDP\15FC_ExpenditureReport_24-25\consolidated_xvfc_2024_25.xlsx", sheet("Consolidated") firstrow clear

replace VillagePanchayatandEquivalent = upper(VillagePanchayatandEquivalent)
replace District = upper(District)
replace Block = upper(Block)

rename District DistrictName
rename Block SubDistrictName
rename VillagePanchayatandEquivalent GramPanchayatName

drop if missing(GramPanchayatName)

merge 1:1 DistrictName SubDistrictName GramPanchayatName using "C:\Users\ankita\Dropbox\Peer Effects and Role Models\Analysis_Experiment\1_Raw\Input\UGP.dta", gen(merge_ugp)

keep if merge_ugp == 3
*/


use "C:\Users\ankita\Dropbox\Peer Effects and Role Models\GPDP Analysis (For Non-Peer)\ugp_xvfc_2024_25.dta", clear

rename ugp UGP

merge 1:1 UGP using "${db}/3_Analyse/Input/Administrative Data/NREGA/GPExtendedControls_clean.dta", ///
    keepusing(Tot_Pop2011C Villages TotalArea DistHQDis NearTownDis Tot_Pop2011C_100 SCGPProp2011C) gen(mx1)
keep if mx1 == 3

rename UGP ugp

merge 1:1 ugp using "C:\Users\ankita\Dropbox\Peer Effects and Role Models\Analysis_Experiment\1_Raw\Input\Raw Excel Politician Files\Reservation_Pop_F.dta", keepusing(sc_2016 sc_reserved_2016 women_2016) gen(mx2)

keep if mx2 ==3


**** Total expenditure correlation with :

* Villages
reg consolidated_total_expenditure Villages, abs(districtname)

* Total Area
reg consolidated_total_expenditure TotalArea, abs(districtname)

* Distance to District Headquarters
reg consolidated_total_expenditure DistHQDis, abs(districtname)

* Distance to nearest town
reg consolidated_total_expenditure NearTownDis, abs(districtname)

* Total Population
reg consolidated_total_expenditure Tot_Pop2011C_100, abs(districtname)

* SCG Proportion
reg consolidated_total_expenditure SCGPProp2011C, abs(districtname)


* Create variable for Spending per capita
gen exp_tot_per_cap = consolidated_total_expenditure/Tot_Pop2011C

*** Per Capita Expenditure correlation with

* Villages
reg exp_tot_per_cap Villages, abs(districtname)

* Total Area
reg exp_tot_per_cap TotalArea, abs(districtname)

* Distance to District Headquarters
reg exp_tot_per_cap DistHQDis, abs(districtname)

* Distance to nearest town
reg exp_tot_per_cap NearTownDis, abs(districtname)

* SCG Proportion
reg exp_tot_per_cap SCGPProp2011C, abs(districtname)

* SC 2006
reg exp_tot_per_cap sc_2016, abs(districtname)

* SC Reserved GP
reg exp_tot_per_cap sc_reserved_2016, abs(districtname)



*** Unspent 

gen unspent_over_total = consolidated_total_unspent_balan/consolidated_total_expenditure


* Villages
reg unspent_over_total Villages, abs(districtname)

* Total Area
reg unspent_over_total TotalArea, abs(districtname)

* Distance to District Headquarters
reg unspent_over_total DistHQDis, abs(districtname)

* Distance to nearest town
reg unspent_over_total NearTownDis, abs(districtname)

* SCG Proportion
reg unspent_over_total SCGPProp2011C, abs(districtname)

* SC 2016
reg unspent_over_total sc_2016, abs(districtname)

* SC Reserved GP
reg unspent_over_total sc_reserved_2016, abs(districtname)

* Women 2016
reg unspent_over_total women_2016, abs(districtname)
