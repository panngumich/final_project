############# Name: NENG PAN  #############
############# Uniqname: panng #############
import requests
import json
import sqlite3
import secrets
import plotly.graph_objs as go

CACHE_LIST = []
client_key = secrets.ACCESS_KEY

species_list = ['orca', 'minke', 'gray whale', 'humpback', 'atlantic white-sided dolphin', 'pacific white-sided dolphin',
                'dalls porpoise', 'harbor porpoise', 'harbor seal', 'northern elephant seal', 'southern elephant seal', 
                'california sea Lion', 'steller sea lion', 'sea otter', 'other', 'unknown']


##### Request data
def request_report(species=None,start_date=None,end_date=None):
    endpoint = "http://hotline.whalemuseum.org/api.json"
    parameter = {
        "species":species,
        "since":start_date,
        "until":end_date,
        "limit":1000
        }
    response = requests.get(endpoint,params=parameter).json()
    return response

def request_picture(species):
    endpoint = "https://api.unsplash.com/search/photos?query=" + species + "&client_id=" + client_key
    response = requests.get(endpoint).json()

    page = response['total_pages']
    picture_dict = {}
    i = 1
    results = []
    while (i <= page):
        response_all = requests.get(endpoint + "&page=" + str(i)).json()
        i += 1
        for item in response_all['results']:
            results.append(item)

    picture_dict[species] = results
    return picture_dict


##### Cache data
def make_request_using_cache(request_species):
    if (request_species in CACHE_LIST):
        print("Using cache")
    else:
        print("Fetching")
        populate_pictures_record(request_species)


##### Create Database
def create_table_report():
    conn = sqlite3.connect("whalesightreports.sqlite")
    cur = conn.cursor()

    create_sql = '''
        CREATE TABLE IF NOT EXISTS "Reports" (
            "Id"          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "Species"     TEXT NOT NULL,
            "SpeciesId"   INTEGER,
            "Quantity"    INTEGER,
            "Location"    TEXT,
            "Latitude"    TEXT NOT NULL,
            "Longitude"   TEXT NOT NULL,
            "SightedDate" TEXT NOT NULL,
            "Year"        TEXT NOT NULL,
            "Month"       TEXT NOT NULL,
            "Date"        TEXT NOT NULL
        );
    '''
    cur.execute(create_sql)
    conn.commit()

def create_table_picture():
    conn = sqlite3.connect("whalesightreports.sqlite")
    cur = conn.cursor()

    create_sql = '''
        CREATE TABLE IF NOT EXISTS "Pictures" (
            "Id"          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "PictureId"   INTEGER NOT NULL,
            "PictureUrl"  TEXT NOT NULL,
            "Author"      TEXT,
            "Description" TEXT,
            "Likes"       INTEGER,
            "CreateDate"  TEXT
        );
    '''
    cur.execute(create_sql)
    conn.commit()

def delete_table_report():
    conn = sqlite3.connect("whalesightreports.sqlite")
    cur = conn.cursor()

    drop_sql = '''
        DROP TABLE IF EXISTS "Reports"
    '''
    cur.execute(drop_sql)
    conn.commit()


##### Update Database
def populate_reports(sql_list):
    conn = sqlite3.connect("whalesightreports.sqlite")
    cur = conn.cursor()

    insert_sql = '''
        INSERT INTO Reports (Species, SpeciesId, Quantity, Location, Latitude, Longitude, SightedDate, Year, Month, Date)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    '''   
    cur.execute(insert_sql,sql_list)
    conn.commit()

def populate_report_record(species, start_date, end_date):
    delete_table_report()
    create_table_report()
    for record in request_report(species, start_date, end_date):
        speciesid = species_list.index(record['species']) + 1
        year = record['sighted_at'].split('-')[0]
        month = record['sighted_at'].split('-')[1]
        date = record['sighted_at'].split('-')[2][:2]
        record_list = [record['species'], speciesid, record['quantity'], record['location'], record['latitude'], record['longitude'], record['sighted_at'], year, month, date]
        populate_reports(record_list)


def populate_pictures(sql_list):
    conn = sqlite3.connect("whalesightreports.sqlite")
    cur = conn.cursor()

    insert_sql = '''
        INSERT INTO Pictures (PictureId, PictureUrl, Author, Description, Likes, CreateDate)
        VALUES (?,?,?,?,?,?)
    '''
    cur.execute(insert_sql,sql_list)
    conn.commit()

def populate_pictures_record(species):
    CACHE_LIST.append(species)
    picture_all = request_picture(species)
    pictureid = species_list.index(species) + 1

    for pic in picture_all[species]:
        record_list = [pictureid, pic['urls']['raw'], pic['user']['name'], pic['description'], pic['likes'], pic['created_at']]
        populate_pictures(record_list)
        


##### SQL Query
def make_query(query):
    connection = sqlite3.connect("whalesightreports.sqlite")
    cursor = connection.cursor() 
    result = cursor.execute(query).fetchall()
    connection.close()
    return result

def query_for_distribution(species, start_date, end_date):
    query = """
    SELECT Longitude, Latitude
    FROM Reports
    WHERE Species = '""" + species + "' AND SightedDate <= '" + end_date + "' AND SightedDate >= '" + start_date + "'"
    return query

def query_for_most_sighted_species(start_date=None, end_date=None):
    if start_date:
        if end_date:
            query = """
            SELECT Species, COUNT(*)
            FROM Reports
            WHERE SightedDate <= '""" + end_date + "' AND SightedDate >= '" + start_date + "' GROUP BY Species ORDER BY COUNT(*) DESC Limit 5"
        else:
            query = """
            SELECT Species, COUNT(*)
            FROM Reports
            WHERE SightedDate >= '""" + start_date + "' GROUP BY Species ORDER BY COUNT(*) DESC Limit 5"
    else:
        query = """
            SELECT Species, COUNT(*)
            FROM Reports
            WHERE SightedDate <= '""" + end_date + "' GROUP BY Species ORDER BY COUNT(*) DESC Limit 5"       
    return query

def query_for_most_sighted_time(field_name,species=None):
    if species:
        query = "SELECT "+ field_name + ", COUNT(*) " + """
        FROM Reports
        WHERE Species = '""" + species + "' GROUP BY " + field_name + " ORDER BY COUNT(*) DESC Limit 10"
    else:
        query = "SELECT "+ field_name + ", COUNT(*) " + """
        FROM Reports
        GROUP BY """ + field_name + " ORDER BY COUNT(*) DESC Limit 10"
    return query

def query_for_most_liked_pictures(species):
    speciesid = species_list.index(species) + 1
    query = """
    SELECT Author, Likes, CreateDate, PictureUrl
    FROM Pictures
    WHERE PictureId = '""" + str(speciesid) + "' Order by Likes DESC Limit 10"
    return query

def query_for_most_recent_pictures(species):
    speciesid = species_list.index(species) + 1
    query = """
    SELECT Author, Likes, CreateDate, PictureUrl
    FROM Pictures
    WHERE PictureId = '""" + str(speciesid) + "' Order by CreateDate DESC Limit 10"
    return query

##### Plotly
def draw_plotly(xvals, yvals):
    bar_data = go.Bar(x = xvals,y = yvals)
    fig = go.Figure(data = bar_data)
    fig.write_html("plotly.html")

##### Interact
def service_select(num):
    if num.isdigit():
        if num == '1':
            print("\n======================================= 1 =======================================")
            start = input("Please enter the start time of the period you want to check: ")
            end = input("Please enter the ending time of the period you want to check: ")
            print("================================================================================")
            print("Most frequently sighted whale species from " + start + " to " + end + ":\n")
            
            populate_report_record(species=None, start_date=start, end_date=end)
            result = make_query(query_for_most_sighted_species(start, end))
            
            xvals = []
            yvals = []
            for item in result:
                print("Most sighted species: " + item[0] + ", sighted " + str(item[1]) + " times.")
                xvals.append(item[0])
                yvals.append(item[1])
            draw_plotly(xvals, yvals)

        elif num == '2':
            print("\n======================================= 2 =======================================")
            species = input("Please enter a species name you want to check (if there is no exact species you want to check, please press 'Enter' to skip): ")
            start = input("Please enter the start time of the period you want to check: ")
            end = input("Please enter the ending time of the period you want to check: ")
            field_name = input("Please enter the type of the time period you want to check (e.g: Year/Month/Date): ")
            if species:
                print("================================================================================")
                print("Time periods when " + species + " are most often seen:\n")
            else:
                print("================================================================================")
                print("Time periods when whales are most often seen:\n")
            populate_report_record(species, start_date=start, end_date=end)
            result = make_query(query_for_most_sighted_time(field_name,species))
            
            xvals = []
            yvals = []
            for item in result:
                print("Most sighted " + field_name + ": " + item[0] + ", sighting " + str(item[1]) + " records.")
                xvals.append(item[0])
                yvals.append(item[1])
            draw_plotly(xvals, yvals)
        
        elif num == '3':
            print("\n======================================= 3 =======================================")
            species = input("Please enter a species name you want to check: ")
            sort_key = input("Please enter the sort_key (likes/relevance): ")
            
            if sort_key == 'likes':
                print("================================================================================")
                print("Most liked 10 pictures of " + species + ":\n")
                
                make_request_using_cache(species)
                result = make_query(query_for_most_liked_pictures(species))
                print("        Author        | Likes | CreateDate  |   PictureUrl")
                row = "{num:<1d}\t{author:<10s}\t{likes:<4d}\t{date:<6s}\t{url:<40s}".format    
                i = 1
                for item in result:
                    print(row(num=i, author=item[0], likes=item[1], date=item[2][:10], url=item[3]))
                    i += 1

            else:
                print("================================================================================")
                print("Most recent 10 pictures of " + species + ":\n")
                
                make_request_using_cache(species)
                result = make_query(query_for_most_recent_pictures(species))
                print("        Author        | Likes | CreateDate  |   PictureUrl")
                row = "{num:<1d}\t{author:<10s}\t{likes:<4d}\t{date:<6s}\t{url:<40s}".format    
                i = 1
                for item in result:
                    print(row(num=i, author=item[0], likes=item[1], date=item[2][:10], url=item[3]))
                    i += 1
        
        elif num == '4':
            print("\n======================================= 4 =======================================")
            species = input("Please enter a species name you want to check: ")
            start = input("Please enter the start time of the period you want to check: ")
            end = input("Please enter the ending time of the period you want to check: ")
            print("================================================================================")
            print("Distribution map of " + species + " observed from " + start + " to " + end + ":\n")
            
            populate_report_record(species=species, start_date=start, end_date=end)
            result = make_query(query_for_distribution(species, start, end))
            for item in result:
                print(item)
        
        else:
            print("Please enter a valid serial number.")
    
    else:
        print("Please enter an integer.")

############################ interactive part ############################ 
create_table_report()
create_table_picture()

while True:
    print("\n--------------------------------------- Menu ---------------------------------------")
    print("Welcome! There are four services to choose from: ")
    print("""
    1. Search for the top 5 most frequently sighted whale species during a certain period of time
    2. Search for the time periods when certain types of whales are most often seen
    3. Enjoy the top 10 pictures on Unsplash of a certain type of marine mammal
    4. Explore the distribution map of certain types of whales observed in a certain period of time
    """)
    
    service_num = input('Please enter the serial number of the service you want to select: ')
    service_select(service_num)         