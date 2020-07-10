import graphene
import graphql_jwt

import catalog.schema

class Query(
    catalog.schema.Query,
    graphene.ObjectType,
):    
    pass

class Mutation(
    catalog.schema.Mutation,
    graphene.ObjectType,
):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
