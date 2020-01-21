from schema import Schema, And, Use, Optional

schema = Schema([{'name': And(str, len),
                  'age': And(Use(int), lambda n: 18 <= n <= 99),
                  Optional('gender'): And(str, Use(str.lower),
                                          lambda s: s in ('squid', 'kid'))}])
