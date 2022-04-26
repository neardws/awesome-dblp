import dblp
from multiprocessing import Pool


if __name__ == '__main__':
    keywords = ['survey', 'review']
    venue_names = ['JSAC', 
                    'TMC', 
                    'TON', 
                    'Conference on Applications, Technologies, Architectures, and Protocols for Computer Communication', 
                    'MobiCom', 
                    'IEEE Conference on Computer Communications', 
                    'NSDI']
    query_number = 5000
    maximum_query_number = 50
    
    pool = Pool(processes=5)
    for venue_name in venue_names:
        pool.apply_async(dblp.search_by_keywords_venues, (keywords, [venue_name], query_number, maximum_query_number))
    print('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    print('All subprocesses done.')

