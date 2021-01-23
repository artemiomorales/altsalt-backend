import graphene

import catalog.schema.schema


class Query(
    catalog.schema.schema.Query,
    graphene.ObjectType,
):    
    pass


class Mutation(
    catalog.schema.schema.Mutation,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
