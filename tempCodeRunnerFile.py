pool = Pool(processes=4)
    # for venue_name in venue_names:
    #     pool.apply_async(dblp.search_by_keywords_venues, (keywords, [venue_name], query_number, maximum_query_number))
    # print('Waiting for all subprocesses done...')
    # pool.close()
    # pool.join()
    # print('All subprocesses done.')