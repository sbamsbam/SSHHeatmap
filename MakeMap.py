# Author: Mees Altena, 24-04-2020                                                                                            
# Rev: Matteo Altomare, George Adrian Munteanu 10-10-2020                                                                    
# Licence: MIT                                                                                                               
import re                                                                                                                    
import os                                                                                                                    
import requests                                                                                                              
import folium                                                                                                                
from folium import plugins# big map                                                                                          
                                                                                                                             
from folium.plugins import HeatMap                                                                                           
from folium.plugins import MarkerCluster                                                                                     
import ipinfo                                                                                                                
import sys                                                                                                                   
import time                                                                                                                  
from collections import Counter                                                                                              
import operator                                                                                                              
                                                                                                                             
# import plugin from folium                                                                                                  
mini_map = plugins.MiniMap(toggle_display=True)# add the mini map to the big map                                             
# Set a default api key here if you're not using sys arguments.                                                              
api_key = ""                                                                                                                 
                                                                                                                             
# Filename of the txt with the output of: grep "authentication failure\| Failed password" /var/log/auth.log > failed_attempts
.txt                                                                                                                         
try:                                                                                                                         
    filename = sys.argv[1]                                                                                                   
except IndexError:                                                                                                           
    if(api_key == ""):                                                                                                       
        print("Usage: SSHHeatmap.py <source_filename> <api key> <attempts_threshold> <heatmap_filename>")                    
        print("To run SSHHeatmap without arguments, manually set an api key.")                                               
        quit()                                                                                                               
    filename = "failed_attempts.txt"                                                                                         
    pass                                                                                                                     
                                                                                                                             
# ipinfo.io api key                                                                                                          
try:                                                                                                                         
    api_key = sys.argv[2]                                                                                                    
except IndexError:                                                                                                           
    if(api_key == ""):                                                                                                       
        raise IndexError("API key not found. Please pass your ipinfo.io api key as the second argument, or set it manually.")
                                                                                                                             
# minimum login attempts per ip required to include it in the heatmap                                                        
try:                                                                                                                         
    min_attempts = int(sys.argv[3])                                                                                          
except IndexError:                                                                                                           
    min_attempts = 30                                                                                                        
    pass                                                                                                                     
                                                                                                                             
# what filename the heatmap should be saved as.                                                                              
try:                                                                                                                         
    heatmap_filename = sys.argv[4]                                                                                           
except IndexError:                                                                                                           
    heatmap_filename = 'heatmap.html'                                                                                        
    pass                                                                                                                     
                                                                                                                             
# create handler to interface with API                                                                                       
ip_handler = ipinfo.getHandler(api_key)                                                                                      
                                                                                                                             
# read the file, split on newlines into array, return list of ips                                                            
def read_file_get_ips(filename):                                                                                             
    with open(filename) as f:                                                                                                
        f_a = f.read().split('\n')                                                                                           
        # get array with only the ips                                                                                        
        # Use a regex to match and extract ips                                                                               
        p = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')                                                                 
        ips=[]                                                                                                               
        for x in f_a:                                                                                                        
            match = p.search(x)                                                                                              
            if match:                                                                                                        
                ip = match.group(0)                                                                                          
                ips.append(ip)                                                                                               
                                                                                                                             
        print('Read file ' + filename + ' and got ' + str(len(ips)) + ' login attempts.')                                    
        return ips                                                                                                           
                                                                                                                             
# Returns a list with the items in the passed list that occur at least min_attempts times.                                   
def get_applicable_ips(ips):                                                                                                 
    counts = Counter(ips).most_common()                                                                                      
    meet_minimum = [x[0] for x in counts if x[1] > min_attempts]                                                             
    print('No. of ips with at least ' + str(min_attempts) + ' login attempts: ' + str(len(meet_minimum)))                    
    return meet_minimum                                                                                                      
                                                                                                                             
# Call ipinfo api per api to get coordinates.                                                                                
def get_ip_coordinates(ips):                                                                                                 
                                                                                                                             
    print('Fetching coordinates...')                                                                                         
    if(len(ips) > 500):                                                                                                      
        print("Fetching coordinates for > 500 IP's. Please consider using your own (free) ipinfo API key if you are not alrea
dy.")                                                                                                                        
                                                                                                                             
    # split the list of ips into batches of 100 (or less, if the list is smaller)                                            
    batches = [ips[x:x+100] for x in range(0, len(ips), 100)]                                                                
    coords = []                                                                                                              
    coordinates_with_ip = []                                                                                                 
    counter = 0                                                                                                              
    start = time.process_time()                                                                                              
    for batch in batches:                                                                                                    
        # send the request to the api and get the values                                                                     
        api_batch_results = ip_handler.getBatchDetails(batch).values()                                                       
        for element in api_batch_results:                                                                                    
            location = element.get('loc')                                                                                    
            if location is not None:                                                                                         
                ip = element.get('ip')                                                                                       
                # split the coords into a list with lat and lon                                                              
                coords.append(location.split(','))                                                                           
                # split the coords into a list with lat and lon and append the ip address, in order to add the Marker        
                list_location = location.split(',')                                                                          
                list_location.append(ip)                                                                                     
                coordinates_with_ip.append(list_location)                                                                    
                                                                                                                             
        print("Fetched " + str(len(coords)) + "/" + str(len(ips)) + " coordinates in " + str(round(time.process_time() - star
t, 3)) + " seconds.")                                                                                                        
                                                                                                                             
    return coords, coordinates_with_ip                                                                                       
                                                                                                                             
def generate_and_save_heatmap(coords, coordinates_with_ip):                                                                  
    # generate and save heatmap                                                                                              
    m = folium.Map(tiles="OpenStreetMap", location=[20,10], zoom_start=2)                                                    
    fg=folium.FeatureGroup(name='My Points', show=False)                                                                     
    marker_cluster = MarkerCluster(name = 'Marker').add_to(m)                                                                
    mini_map = plugins.MiniMap(toggle_display=True)# add the mini map to the big map                                         
                                                                                                                             
    m.add_child(mini_map)                                                                                                    
    HeatMap(data= coords, radius=15, min_opacity = 0.1,  blur=20, max_zoom=3, max_val=50, name = 'Heatmap').add_to(m)        
                                                                                                                             
    # I can add marker one by one on the map                                                                                 
    for latlon in coordinates_with_ip:                                                                                       
        folium.Marker(location= latlon[0:2], popup='Source ip='+ str(latlon[2]), tooltip = "apility.io or virustotal ip API",
  icon=folium.Icon(color='red', icon='info-sign')).add_to(marker_cluster)                                                    
                                                                                                                             
    folium.LayerControl().add_to(m)                                                                                          
    m.save(heatmap_filename)                                                                                                 
    print('Done. heatmap saved as ' + heatmap_filename)                                                                      
    return                                                                                                                   
                                                                                                                             
def main():                                                                                                                  
    ips = read_file_get_ips(filename)                                                                                        
    ips_count = get_applicable_ips(ips)                                                                                      
    coords, coordinates_with_ip = get_ip_coordinates(ips_count)                                                              
    generate_and_save_heatmap(coords, coordinates_with_ip)                                                                   
                                                                                                                             
main()               