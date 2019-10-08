from testify import *

from silverpop import API
from silverpop.exceptions import AuthException, ResponseException

from test_config import *

class GoodLoginTestCase(TestCase):
    @class_setup
    def init_api_object(self):
        self.good_api = API(url, username, password)
    
    def test_good_login_sets_session_id(self):
        assert_not_equal(self.good_api.sessionid, None)
    
class BadLoginTestCase(TestCase):
    def test_bad_login_raises_exception(self):
        assert_raises(AuthException, API, url, 'test', 'test')

class DataRetrievalTestCase(TestCase):
    @class_setup
    def init_api_object(self):
        self.api = API(url, username, password, sessionid)
        self.data = self.api.get_user_info(list_id, retrieve_email)
    
    def test_valid_address_retrieval(self):
        assert_equal(retrieve_email, self.data['EMAIL'])
    
    def test_invalid_address_retrieval(self):
        assert_raises(ResponseException, self.api.get_user_info, list_id,
                                                              'fake@fake.tld')

#class RetryTestCase(TestCase):
#    '''This test case is not working because the machine I'm using to write 
#    this is whitelisted and the API does not require authentication from
#    whitelisted machines.'''
#    
#    @setup
#    def init_api_object(self):
#        self.api = API(url, username, password, sessionid='gogogadget')
#    
#    def test_retrieval_retries(self):
#        data = self.api.update_user(list_id, retrieve_email,
#                                                {'PurchasedDomainCount': 72})
#        assert_equal(data, True)
#    
#    def test_retrieval_throws_auth_exception_if_auth_fails(self):
#        self.api.password = 'failed'
#        assert_raises(AuthException, self.api.update_user, list_id,
#                                retrieve_email, {'PurchasedDomainCount': 90})


class AddAndRemoveUserTestCase(TestCase):
    @class_setup
    def init_api_object(self):
        from time import time
        self.api = API(url, username, password, sessionid)
        self.email = 'test%s@fake.tld' % time()
        
        # Create the user
        self.created = self.api.add_user(list_id, self.email,
                                                  {'Currency': 'USD'})
        self.retrieved_currency = \
            self.api.get_user_info(list_id, self.email)['COLUMNS']['Currency']
    
        # Remove the user
        self.removed = self.api.remove_user(list_id, self.email)
    
    def test_user_created(self):
        assert_equal(self.created, True)
    
    def test_retrieval_of_new_user_succeeded(self):
        assert_in('USD', self.retrieved_currency)
    
    def test_user_removed(self):
        assert_equal(self.removed, True)
    
    def test_retrieval_of_removed_user_fails(self):
        assert_raises(ResponseException,
                                  self.api.get_user_info, list_id, self.email)
    
class UpdateUserTestCase(TestCase):
    @class_setup
    def init_api_object(self):
        self.api = API(url, username, password, sessionid)
        self.user_info = self.api.get_user_info(list_id, retrieve_email)
        self.domain_count = \
                            self.user_info['COLUMNS']['PurchasedDomainCount']
        self.new_domain_count = 0 if self.domain_count == '' else \
                                                    int(self.domain_count) + 1
                                                    
        self.result = self.api.update_user(list_id, retrieve_email,
                               {'PurchasedDomainCount':self.new_domain_count})
        
        self.updated_user_info = \
                               self.api.get_user_info(list_id, retrieve_email)
        self.updated_domain_count = \
                     self.updated_user_info['COLUMNS']['PurchasedDomainCount']
                     
    def test_data_param_required(self):
        assert_raises(AssertionError, self.api.update_user,
                                                  list_id, retrieve_email, {})
    
    def test_data_param_must_be_dict(self):
        assert_raises(AssertionError, self.api.update_user,
                                                list_id, retrieve_email, [1,])
    
    def test_update_succeeded(self):
        assert_equal(self.result, True)
        assert_equal(self.updated_domain_count, str(self.new_domain_count))
        

class OptOutTestCase(TestCase):
    @class_setup
    def init_api_object(self):
        self.api = API(url, username, password, sessionid)
        self.api.add_user(list_id, 'optout@fake.tld')
        
        self.opt_out = self.api.opt_out_user(list_id, 'optout@fake.tld')
        
        self.user_data = self.api.get_user_info(list_id, 'optout@fake.tld')
        
        self.api.remove_user(list_id, 'optout@fake.tld')
    
    def test_opt_out_call_success(self):
        assert_equal(self.opt_out, True)
    
    def test_silverpop_says_opted_out(self):
        assert_not_equal(self.user_data['OptedOut'], '')
    
    