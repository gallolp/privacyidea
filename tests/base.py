import unittest
import json
from privacyidea.app import create_app
from privacyidea.models import db
from privacyidea.lib.resolver import (save_resolver)
from privacyidea.lib.realm import (set_realm)
from privacyidea.lib.user import User
from privacyidea.lib.auth import create_db_admin

PWFILE = "tests/testdata/passwords"


class MyTestCase(unittest.TestCase):
    resolvername1 = "resolver1"
    resolvername2 = "Resolver2"
    resolvername3 = "reso3"
    realm1 = "realm1"
    realm2 = "realm2"
    serials = ["SE1", "SE2", "SE3"]
    otpkey = "3132333435363738393031323334353637383930"

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        # Create an admin for tests.
        create_db_admin(cls.app, "testadmin", "admin@test.tld", "testpw")

    def setUp_user_realms(self):
        # create user realm
        rid = save_resolver({"resolver": self.resolvername1,
                               "type": "passwdresolver",
                               "fileName": PWFILE})
        self.assertTrue(rid > 0, rid)

        (added, failed) = set_realm(self.realm1,
                                    [self.resolvername1])
        self.assertTrue(len(failed) == 0)
        self.assertTrue(len(added) == 1)

        user = User(login="root",
                    realm=self.realm1,
                    resolver=self.resolvername1)

        user_str = "%s" % user
        self.assertTrue(user_str == "<root.resolver1@realm1>", user_str)

        self.assertFalse(user.is_empty())
        self.assertTrue(User().is_empty())

        user_repr = "%r" % user
        expected = ("User(login='root', realm='realm1', resolver='resolver1')")
        self.assertTrue(user_repr == expected, user_repr)

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        
    def setUp(self):
        self.authenticate()
        
    def authenticate(self):
        with self.app.test_request_context('/auth',
                                           data={"username": "testadmin",
                                                 "password": "testpw"},
                                           method='POST'):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = json.loads(res.data).get("result")
            self.assertTrue(result.get("status"), res.data)
            self.at = result.get("value").get("token")
