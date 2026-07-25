# CV -> project mapping with an explicit confidence for each.
# CONFIDENT  = the CV names this project unambiguously (street, name, or place)
# AMBIGUOUS  = the CV has two or more entries that could be this one
# ABSENT     = nothing in the CV corresponds
M = {
 "hotel-savaneti-in-ikalto-georgia":      ("2014–2018","CONFIDENT","'Hotel Savaneti in Ikalto' 3,500m²"),
 "condominium-on-aleksidze-str-tbilisi-georgia": ("2015–2018","CONFIDENT","'Residence on Alexidze str.' 5,000m²"),
 "villa-at-lisi-lake-tbilisi":            ("2011","CONFIDENT","'Private villa on Lisi lake' 800m²"),
 "restaurant-argo-in-zugdidi":            ("2015","CONFIDENT","'Restaurant Argo in Zugdidi' 750m²"),
 "yezidi-cultural-center-in-tbilisi":     ("2014–2015","CONFIDENT","'Yezidi Culture Center and Temple' 1,700m² (note: a site photo is date-stamped 2017)"),
 "iraki-embassy-tbilisi-project":         ("2014","CONFIDENT","'Tender winner project of Embassy of Iraq'"),
 "center-of-allergy-immunology-tbilisi-georgia": ("2014","CONFIDENT","'Center of Allergy and Immunology' 200m²"),
 "hotel-tornado-project":                 ("","CONFIDENT","listed under Ongoing Works — left blank rather than dated"),
 "hotel-wave-project":                    ("","CONFIDENT","listed under Ongoing Works — left blank rather than dated"),

 "cgc-office-in-rustavi-georgia":         ("","AMBIGUOUS","CV has CGC Rustavi twice: 2013 (1,000m²) and 2010 (400m²)"),
 "cgc-office-renovation":                 ("","AMBIGUOUS","same two CGC entries — which is the reconstruction?"),
 "villa-in-tsavkisi-georgia":             ("","AMBIGUOUS","CV has Tsavkisi twice: 2015 (300m²) and 2008"),
 "condominium-1":                         ("","AMBIGUOUS","possibly the 19-floor Saburtalo block (2006–2009); photos suggest ~15 floors"),
 "condominium":                           ("","AMBIGUOUS","a site photo is date-stamped 2021; no clear CV entry"),
 "hotel-project":                         ("","AMBIGUOUS","could be Tskneti (2012, 1,500m²) or Squri (2013, 7,000m²)"),
 "old-house-reconstruction":              ("","AMBIGUOUS","Saguramo appears as a 1998 villa and as ongoing work"),
 "old-hotel-renovation-project":          ("","AMBIGUOUS","renders read 'Grand Hotel'; possibly the ongoing Marjan Hotel, but that is described as old-centre, not waterfront"),
 "two-vllas-in-krtsanisi-tbilisi-georgia":("","AMBIGUOUS","CV lists Krtsanisi only under ongoing works, undated"),
 "allergy-immunology-polyclinic-tbilisi-georgia": ("","AMBIGUOUS","CV has one allergy/immunology entry (2014); this looks like a separate, unbuilt design"),

 "cafe-project-at-eliava-str-in-tbilisi-georgia": ("","ABSENT","no cafe on Eliava str. in the CV"),
 "condominium-project":                   ("","ABSENT","no matching entry"),
 "hotel-project-in-bakuriani":            ("","ABSENT","Bakuriani is not mentioned in the CV"),
 "restaurant-in-dusheti-georgia":         ("","ABSENT","CV lists a villa in Dusheti (2012), not a restaurant"),
 "villa-in-tabakhmela-georgia":           ("","ABSENT","Tabakhmela is not mentioned in the CV"),
 "orthodox-curch-project":                ("","ABSENT","no matching entry"),
 "interior":                              ("","ABSENT","CV lists many interiors by client name; cannot match to photos"),
 "interior-1":                            ("","ABSENT","same"),
 "interior-2":                            ("","ABSENT","same"),
 "interior-3":                            ("","ABSENT","same"),
 "interior-4":                            ("","ABSENT","Hotel 'Sachveno' is not named in the CV"),
 "interior-5":                            ("","ABSENT","same"),
 "interrior":                             ("","ABSENT","same"),
}
