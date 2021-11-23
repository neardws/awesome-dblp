import dblp

# author_list = dblp.search('author', 'kai liu')
# print(len(author_list))
# # for index, author in enumerate(author_list):
# #     print(index)
# #     print(author.publications[0].title)

# author0 = author_list[0]
# print(author0.name)
# print(author0.data)
# print(len(author0.publications))
# print(author0.publications[0].title)
# print(author0.publications[0].journal)
# print(author0.publications[0].year)
# print(author0.publications[0].month)
# print(author0.publications[0].school)
venue = dblp.search('venue', 'TMC')
# print(venue[0].acronym)
# print(venue[0].type)
# print(venue[0].name)
# print(venue[0].url)
print(venue[0].publications[0].title)
print(len(venue[0].publications))
# print(len(venue_list))