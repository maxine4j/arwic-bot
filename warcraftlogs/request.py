from private import warcraftlogs_pub_key
import urllib.request


api_version = "v1"


def request(path):
    return urllib.request.urlopen("https://www.warcraftlogs.com:443/{}/{}?api_key={}".format(api_version, path, warcraftlogs_pub_key)).read()


def get_zones():
    '''
    Gets an array of Zone objects. Each zone corresponds to a raid/dungeon instance in the game and has its own set of encounters.
    '''
    return request("zones")


def get_classes():
    '''
    Gets an array of Class objects. Each Class corresponds to a class in the game.
    '''
    return request("classes")


def get_encounter_rankings(*args, **kwargs):
    '''
    Gets an object that contains a total count and an array of EncounterRanking 
    objects and a total number of rankings for that encounter. 
    Each EncounterRanking corresponds to a single character or guild/team.
    :param encounterID: The encounter to collect rankings for. Encounter IDs can be obtained using a /zones request.
    :param metric:      The metric to query for. Valid fight metrics are 'speed', 'execution' and 'feats'. 
                        Valid character metrics are 'dps', 'hps', 'bossdps, 'tankhps', or 'playerspeed'. 
                        For WoW only, 'krsi' can be used for tank survivability ranks.
    :param size:        The raid size to query for. This is only valid for fixed size raids. 
                        Raids with flexible sizing must omit this parameter.	
    :param difficulty:  The difficulty setting to query for. 
                        Valid difficulty settings are 1 = LFR, 2 = Flex, 3 = Normal,
                        4 = Heroic, 5 = Mythic, 10 = Challenge Mode, 100 = WildStar.
                        Can be omitted for encounters with only one difficulty setting.	
    :param partition:   The partition group to query for. Most zones have only one partition, and this can be omitted.
                        Hellfire Citadel has two partitions (1 for original, 2 for pre-patch). 
                        Highmaul and BRF have two partitions (1 for US/EU, 2 for Asia).	
    :param klass:       The class to query for if a character metric is specified. 
                        Valid class IDs can be obtained from a /classes API request. Optional.	
    :param spec:        The spec to query for if a character metric is specified. 
                        Valid spec IDs can be obtained from a /classes API request. Optional.	
    :param bracket:     The bracket to query for. If omitted or if a value of 0 is specified, 
                        then all brackets are examined. Brackets can be obtained from a /zones API request.	
    :param limit:       The number of results to return at a time. If omitted, a default of 200 is assumed. 
                        Values greater than 5000 are not allowed.	
    :param guild:       An optional guild to filter on. If set, the server and region must also be specified.	
    :param server:      A server to filter on. If set, the region must also be specified. 
                        This is the slug field in Blizzard terminology.	
    :param region:      The short name of a region to filter on (e.g., US, NA, EU).	
    :param page:        The page to examine, starting from 1. If the value is omitted, then 1 is assumed. For example,
                        with a page of 2 and a limit of 300, you will be fetching rankings 301-600.	
    :param filter:      A search filter string, limiting the search to specific classes, specs, 
                        fight durations, raid sizes, etc. 
                        The format should match the string used on the public rankings pages.	
    :return:
    '''
    my_arg = kwargs["my_areg"]
    encounterID, metric, size, difficulty, partition, klass, spec, bracket, limit, guild, server, region, page, filter = kwargs
    '''
    https://www.warcraftlogs.com:443/{}/
    rankings/encounter/{}?
    metric={}&
    size={}&
    difficulty={}&
    partition={}&
    class={}&
    spec={}&
    bracket={}&
    limit={}&
    guild={}&
    server={}&
    region={}&
    page={}&
    filter={}&
    api_key={}
    '''.format(encounterID, metric, size, difficulty, partition, klass, spec, bracket, limit, guild, server, region, page, filter)
    request(api_version, warcraftlogs_pub_key)
