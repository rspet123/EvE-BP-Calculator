import requests
import json
import csv
import pickle

def format_num(number):
    out = number
    post = ""
    if number > 1000:
        post = "K"
        out = number / 1000
    if number > 1000000:
        post = "M"
        out = number / 1000000
    if number > 1000000000:
        post = "B"
        out = number / 1000000000
    return (str(round(out, 2)) + post)

api_url = "https://market.fuzzwork.co.uk/aggregates/?region=60003760&types="

debug = True
rig_prods = {}
id_to_name = {}
name_to_id = {}
products = {}
blueprints = {}
rigs = {}
rig_bps = {}
salvage_ids = {}
rig_mat_bps = {}
isk_eff = {}
# Salvage Group ID: 754
#Create Hash tables for item id/names
with open('SDEResources/invTypes.csv', newline='', encoding='utf8') as itemTypes:
  types = csv.reader(itemTypes)
  for item in types:
      id_to_name[item[0]] = item[2]
      name_to_id[item[2]] = item[0]
      if item[1] == "787":
          rig_bps[item[0]] = item[2]
      if item[1] == "754":
          salvage_ids[item[0]] = item[2]
#Getting blueprint info
with open('SDEResources/industryActivityMaterials.csv', newline='',encoding='utf8') as bps:
  reader = csv.reader(bps)
  for bp in reader:
    if bp[0] not in blueprints:
      blueprints[bp[0]] = []
    else:
      blueprints[bp[0]].append((bp[2],bp[3]))

#Get products info
with open('SDEResources/industryActivityProducts.csv', newline='',encoding='utf8') as prods:
  reader = csv.reader(prods)
  for prod in reader:
      products[prod[0]] = prod[2]
  
    
for bp in rig_bps.keys():
    curr_id = products[bp]
    curr_item = id_to_name[products[bp]]
    if 'Blueprint' not in curr_item:
        #We find all the rigs
        print(curr_item)
        rigs[curr_id] = curr_item

query_string = ""
#Get Rigs market data
for i,rig in enumerate(rigs.keys()):
    query_string += (rig +",")
query1 = api_url + query_string
rigs_market = requests.get(query1)
rigs_data = json.loads(rigs_market.text)

#Get Salvage market data
salvage_query = ""
for salvage in salvage_ids.keys():
    salvage_query += (salvage +",")
query2 = api_url + salvage_query
salvage_market = requests.get(query2)
salvage_data = json.loads(salvage_market.text)

if debug:
    #Rigs Debug
    for rig in rigs_data.keys():
        print(id_to_name[rig])
        print(format_num(float(rigs_data[rig]["sell"]["min"])))
        
    #Salvage Debug
    for salvage in salvage_data.keys():
        print(id_to_name[salvage])
        print(format_num(float(salvage_data[salvage]["sell"]["min"])))

for rig in rig_bps.keys():
    try:
        rig_prods[rig] = blueprints[rig]
    except KeyError:
        print("ERROR IN RIG:")
        print(id_to_name[rig])

if debug:
    for rig in rig_prods:
        tot_cost = 0
        curr_rig = id_to_name[products[rig]]
        if "II Blueprint" not in curr_rig:
            print("\n"+curr_rig)
            for prod in rig_prods[rig]:
                try:
                    print(id_to_name[prod[0]] + " x" + prod[1] +"\t - " + format_num((float(salvage_data[prod[0]]["sell"]["min"]) *int(prod[1])))+ "ƶ")
                    tot_cost += (float(salvage_data[prod[0]]["sell"]["min"]) *int(prod[1]))
                except KeyError:
                    #This means its probably a T2 rig, so we just gotta get the other components, nbd
                    update_t2_comps = requests.get(api_url+prod[0])
                    update_data = json.loads(update_t2_comps.text)
                    salvage_data[prod[0]]=update_data[prod[0]]
                    tot_cost += (float(salvage_data[prod[0]]["sell"]["min"]) *int(prod[1]))
                    print(id_to_name[prod[0]] + " x" + prod[1] +"\t - " + format_num((float(salvage_data[prod[0]]["sell"]["min"]) *int(prod[1]))) + "ƶ")
            mats_price = float(tot_cost)
            sell_cost = float(rigs_data[products[rig]]["sell"]["min"])
            print("Materials: "+format_num(mats_price) + "ƶ")
            print("Rig Sell: "+format_num(sell_cost) + "ƶ")
            margin = (sell_cost - mats_price)/mats_price
            print("Margin: " + format_num(margin * 100) + "%")
            isk_eff[rig] = (margin,products[rig],curr_rig,rig_prods[rig])

print(max(isk_eff))

isk_eff_list = [(isk_eff[key]) for key in isk_eff.keys()]
isk_eff_list.sort(key=lambda x:x[0],reverse = True)


