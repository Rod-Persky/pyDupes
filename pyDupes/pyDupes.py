import hashlib
import os
import sqlite3 as lite
import sys
import shutil

def checksum(filepath):
    fh = open(filepath, 'rb')
    m = hashlib.sha512()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()

def getfilelisting(basepath):
    #filelist is an array of arrays, the inner array is [filename,filepath, filesize]
    #to ensure os compat, using os.path.norm path here instead of normalising elsewhere
    filelist=list()
    print('Info - getfilelisting(',os.path.normpath(basepath),')')
    for root, dirs, files in os.walk(os.path.normpath(basepath), topdown=False):
        for name in files:
            try:
                if "delete" in root:
                    next()
                currentfile=os.path.join(root, name)
                filedetails=(name,currentfile,os.stat(currentfile).st_size)
                filelist.append(filedetails)
            except:
                continue
                    
    return filelist

def update_progress(amtDone):
    sys.stdout.write("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(amtDone * 50), amtDone * 100))
    sys.stdout.flush()

## Functions now defined, do some work
print('Achievement get - Using pyDupe\n')
searchdir = ['F:/PDF Library']
                     



#Get the file listings, initialise filelisting array
try:
    filelisting = list()
    for sdir in searchdir:
        print('Info - Get listing for',sdir)
        sdirfilelisting = getfilelisting(sdir)
        filelisting.extend(sdirfilelisting)
        print('Achievement get - File List for', sdir,len(sdirfilelisting),'( of',len(filelisting),') files long\n')
except NameError:
    print('Searchdir not included for some reason')


#Setup database connection
con = lite.connect('dupbase.db')


#Ensure that the tables required exist
with con:
    cur = con.cursor()
    cur.execute("create table if not exists filelisting (filename text, filepath text, filesize INT)")
    cur.execute("create table if not exists filehashes (filepath text, hash)")
    cur.execute("drop table if exists internaldups")

    #Update the filelisting cache        
    try:
        for sdir in searchdir:
            cur.execute("delete from filelisting where filepath like ? ||'%'",[os.path.normpath(sdir)])
            print('Info - Updating file listing for',sdir)


        cur.executemany("INSERT INTO filelisting VALUES(?, ?, ?)",filelisting)
        print('\nInfo - Inserted new filelisting\n')

        #only commit if there was no error in the above process
        con.commit()
    except:
        print('Errd - Filelisting update failed for some reason, continuing...')
        con.rollback()
        print('Info - Rolled back update')

   
    #Figure out which files need hashing, initialise the filetohash array
    try:
        filestohash = list()
        for sdir in searchdir:
            lengthfth = len(filestohash)
            cur.execute("select filepath from filelisting where filepath not in (select filepath from filehashes) AND filepath like ? || '%'",[os.path.normpath(sdir)])
            filestohash.extend(cur.fetchall())
            dlengthfth = len(filestohash)-lengthfth
            print('Info -',dlengthfth,'files to hash from', sdir)
    except (TypeError, NameError):
        print('Errd - No search directories')

    #Figure out if filestohas has TypeError or zero length
    if filestohash is None or len(filestohash)==0:
        print('Errd - No files needed hashing in searchdir(s)')
        cur.execute("select filepath from filelisting where filepath not in (select filepath from filehashes)")
        filestohash = cur.fetchall()
        if len(filestohash)>0:
            print('Info - Selecting all files in old DB without hash (no filestohash in searchdir(s))')

    #Hash every file in the list of files to hash, give a nice progress bar... set count to 0
    try:
        if len(filestohash)>0:
            print('\nInfo - There are',len(filestohash),'files to hash... Time to do actual work')
            
        count=0
        for listedfile in filestohash:
            count = count+1
            update_progress(count/len(filestohash))
            filehash = (listedfile[0],checksum(listedfile[0]))
            cur.execute("INSERT INTO filehashes VALUES(?, ?)",filehash)
            con.commit()
        print('\nAchievement get - All files hashed')
    except:
        print('Errd - File hash failed')

    print('Achievement get - SQL Basics Done')

    internaldupsq = """select filename, filelisting.filepath, hash from filelisting join filehashes on filelisting.filepath = filehashes.filepath where filelisting.filepath like ? || '%' and filelisting.filepath in (select filepath from filehashes where hash in (select hash from (select filepath, hash from filehashes where filepath in (select filepath from filelisting where filepath like ? || '%'))group by hash having count(hash)>1)) order by hash"""
    for sdir in searchdir:
        internaldups = list()
        cur.execute(internaldupsq,[os.path.normpath(sdir), os.path.normpath(sdir)]) #sdir is used twice
        internaldups = cur.fetchall()
        print('There are',len(internaldups),'files in',sdir,'that will be skipped')
        cur.execute('create table if not exists internaldups (filename text, filepath text, hash)')
        cur.executemany("INSERT INTO internaldups VALUES(?, ?, ?)",internaldups)
        con.commit()
        
        
        
        

    print('\n\n------------- Erasure Time -------------')
    while True:
        count=0
        while True:
            count=0
            for sdir in searchdir:
                count=count+1
                print('[',count,'] = ',sdir)
            try:
                deleteopt=input('\nPlease select the folder where duplicates will be deleted [x]: ')
                testoob = searchdir[(int(deleteopt)-1)]
                break
            except:
                print(deleteopt,'Was not in the given range, please select one that is')


        deletelist = list()
        cur.execute("select filepath from filelisting where filepath in (select filepath from filehashes where hash in (select hash from filehashes where hash not in (select hash from internaldups) and filepath in (select filepath from filelisting) group by hash having (count(hash)>1)) and filepath like ? || '%')",[os.path.normpath(searchdir[(int(deleteopt)-1)])])
        deletelist = cur.fetchall()
        print('\nThere are',len(deletelist),'files to be deleted\n')
        #print('You have selected',searchdir[(int(deleteopt)-1)],end='\t')
        confirm = input('....are you sure you want to? [y/n]: ')

        if confirm=='n':
            print('\n\n\nQuitting')
            con.close()
            raise Exception('Quitting')
        elif confirm =='y':
            break;


        print(confirm,'Was not a valid choice (sorry), please use [y]es or [n]o\n')


    deletepath = os.path.join(os.path.normpath(searchdir[(int(deleteopt)-1)]),'delete/')

    try:
        os.mkdir(deletepath)
    except:
        pass

    count = 0
    for src in deletelist:
        count = count+1
        update_progress(count/len(deletelist))
        try:
            shutil.move(src[0],deletepath)
        except:
            pass


con.close()
print('Done')


#this query will get filenames which have a hash
#select filename, hash from filelisting join filehashes on filelisting.filepath = filehashes.filepath

#this quiery gives filenames with no hash
#select filename from filelisting where filepath not in (select filepath from filehashes)

#this query gives the duplicates
#select filepath, count(hash) as numoccur from filehashes group by hash having (count(hash)>1)

#this query lists out the duplicate files
#select filename, hash from filelisting join filehashes on filelisting.filepath = filehashes.filepath where hash in (select hash from filehashes group by hash having (count(hash)>1))

#this query gives all filepaths starting with input
#select filepath from filelisting where lower(substr(filepath,1,1))="f"

#cur.execute("DROP TABLE IF EXISTS filelisting")

#select filepath from filelisting where filepath in (
#select filepath from filehashes where hash in (
#select hash from filehashes
#where hash not in (select hash from internaldups)
#group by hash having (count(hash)>1)
#) and filepath like 'F%')


#Cou de grace, find duplicate files in a folder and show both of them
#These should be avoided because it really should require the user to
#select which one they wish to keep

#select filename, filelisting.filepath, hash from filelisting
#join filehashes on filelisting.filepath = filehashes.filepath
#where filelisting.filepath like 'F%'
#and filelisting.filepath in
#    (select filepath from filehashes
#     where hash in
#        (select hash from
#            (select filepath, hash
#             from filehashes
#             where filepath in (
#                 select filepath from filelisting where filepath like 'F%')
#             )
#         group by hash having count(hash)>1)
#     )
#order by hash





