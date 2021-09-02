import graphene
from django.contrib.auth import get_user_model
from graphene_django.types import DjangoObjectType
from catalog.models.base import PriceType, article_image_path_from_model, ContentThread
from catalog.models.cms import *
from .schema_base import BaseImageTypeMixin, check_csrf, login_required, IdentityType, FormatType, TagType, \
    DistributionTypeGrapheneType, GenreType, LanguageType, CountryType, PriceGrapheneType, ContentRatingType, \
    NameWithPriorityInput, UserInput, ImageInput, PriceInput, save_image_data_via_model, save_image_data, send_byline_email, \
    TextChoicesType
from catalog.constants import capitalize_string, get_date_from_string
from graphql import GraphQLError
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify


class ArticleBylineType(DjangoObjectType):
    class Meta:
        model = ArticleByline


class ArticleFeaturedImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ArticleFeaturedImage


class EditorialSettingsType(DjangoObjectType):
    class Meta:
        model = EditorialSettings


class ArticleFormatType(DjangoObjectType):
    class Meta:
        model = ArticleFormat
        exclude = ('format',)

    item = graphene.Field(FormatType)

    def resolve_item(self, info):
        return Format.objects.get(id=self.format_id)


class ArticleTagType(DjangoObjectType):
    class Meta:
        model = ArticleTag
        exclude = ('tag',)

    item = graphene.Field(TagType)

    def resolve_item(self, info):
        return Tag.objects.get(id=self.tag_id)


class ArticleDistributionTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = ArticleDistributionType
        exclude = ('distribution_type',)

    item = graphene.Field(DistributionTypeGrapheneType)

    def resolve_item(self, info):
        return DistributionType.objects.get(id=self.distribution_type_id)


class ArticleGenreType(DjangoObjectType):
    class Meta:
        model = ArticleGenre
        exclude = ('genre',)

    item = graphene.Field(GenreType)

    def resolve_item(self, info):
        return Genre.objects.get(id=self.genre_id)


class ArticleLanguageType(DjangoObjectType):
    class Meta:
        model = ArticleLanguage
        exclude = ('language',)

    item = graphene.Field(LanguageType)

    def resolve_item(self, info):
        return Language.objects.get(id=self.language_id)


class ArticleCountryRepresentedType(DjangoObjectType):
    class Meta:
        model = ArticleCountryRepresented
        exclude = ('country',)

    item = graphene.Field(CountryType)

    def resolve_item(self, info):
        return Country.objects.get(id=self.country_id)


class ArticleIdentityRepresentedType(DjangoObjectType):
    class Meta:
        model = ArticleIdentityRepresented
        exclude = ('identity',)

    item = graphene.Field(IdentityType)

    def resolve_item(self, info):
        return Identity.objects.get(id=self.identity_id)


class ArticleType(DjangoObjectType):
    class Meta:
        model = Article
        fields = ('id', 'title', 'subheading', 'preview_text', 'featured_image', 'body', 'post_script',
                  'is_announcement', 'is_featured', 'is_full_bleed', 'price', 'is_confirmed',
                  'seo_title', 'content_rating', 'related_publish_date', 'length', 'is_excerpt')

    slug = graphene.String()
    bylines = graphene.List(ArticleBylineType)
    featured_image = graphene.Field(ArticleFeaturedImageType)
    format_set = graphene.List(ArticleFormatType)
    distribution_type_set = graphene.List(ArticleDistributionTypeGrapheneType)
    genre_set = graphene.List(ArticleGenreType)
    language_set = graphene.List(ArticleLanguageType)
    countries_represented = graphene.List(ArticleCountryRepresentedType)
    identities_represented = graphene.List(ArticleIdentityRepresentedType)
    tag_set = graphene.List(ArticleTagType)
    price = graphene.Field(PriceGrapheneType)
    moderator_authentication = graphene.Boolean()
    thread_set = graphene.List('catalog.schema.schema_comments.ContentThreadType')
    publish_status = graphene.Field(TextChoicesType)
    featured_image_full_bleed_fit = graphene.Field(TextChoicesType)
    featured_image_full_bleed_alignment = graphene.Field(TextChoicesType)

    def resolve_slug(self, info):
        return slugify(self.title)

    def resolve_bylines(self, info):
        return ArticleByline.objects.filter(article_id=self.id)

    def resolve_featured_image(self, info):
        if ArticleFeaturedImage.objects.filter(article=self).exists():
            return ArticleFeaturedImage.objects.get(article=self)
        else:
            return None

    def resolve_format_set(self, info):
        return ArticleFormat.objects.filter(article_id=self.id)

    def resolve_distribution_type_set(self, info):
        return ArticleDistributionType.objects.filter(article_id=self.id)

    def resolve_genre_set(self, info):
        return ArticleGenre.objects.filter(article_id=self.id)

    def resolve_language_set(self, info):
        return ArticleLanguage.objects.filter(article_id=self.id)

    def resolve_countries_represented(self, info):
        return ArticleCountryRepresented.objects.filter(article_id=self.id)

    def resolve_identities_represented(self, info):
        return ArticleIdentityRepresented.objects.filter(article_id=self.id)

    def resolve_tag_set(self, info):
        return ArticleTag.objects.filter(article_id=self.id)

    def resolve_thread_set(self, info):
        return ContentThread.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(Article))

    def resolve_moderator_authentication(self, info):
        if info.context.user.is_authenticated is True and info.context.user.is_moderator is True:
            return True
        return False

    def resolve_publish_status(self, info):
        return {'value': PublishStatus(self.publish_status).value, 'label': PublishStatus(self.publish_status).label}

    def resolve_featured_image_full_bleed_fit(self, info):
        return {'value': ObjectFit(self.featured_image_full_bleed_fit).value,
                'label': ObjectFit(self.featured_image_full_bleed_fit).label}

    def resolve_featured_image_full_bleed_alignment(self, info):
        return {'value': Alignment(self.featured_image_full_bleed_alignment).value,
                'label': Alignment(self.featured_image_full_bleed_alignment).label}



##########
# SCHEMA #
##########

class CMSQuery(graphene.ObjectType):
    featured_articles = graphene.List(ArticleType)
    article_bundle = graphene.List(ArticleType,
                                   exclude_featured=graphene.Boolean(default_value=False),
                                   exclude_unlisted=graphene.Boolean(default_value=True),
                                   exclude_drafts=graphene.Boolean(default_value=True),
                                   )
    article = graphene.Field(ArticleType, id=graphene.String())
    editorial_settings = graphene.Field(EditorialSettingsType)

    def resolve_featured_articles(self, info, **kwargs):
        return Article.objects.filter(is_featured=True)

    def resolve_article_bundle(self, info, **kwargs):
        exclude_featured = kwargs.get('exclude_featured')
        exclude_unlisted = kwargs.get('exclude_unlisted')
        exclude_drafts = kwargs.get('exclude_drafts')

        if not exclude_featured:
            articles = Article.objects.all()
        else:
            articles = Article.objects.filter(is_featured=False)

        if exclude_unlisted is True:
            articles = articles.exclude(publish_status=PublishStatus.UNLISTED)

        if exclude_drafts is True:
            articles = articles.exclude(publish_status=PublishStatus.DRAFT)

        return articles

    def resolve_article(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Article.objects.get(id=int(id))

        return None

    def resolve_editorial_settings(self, info):
        return EditorialSettings.objects.first()


class CreateArticle(graphene.Mutation):
    article = graphene.Field(ArticleType)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info):

        # Disabled for now

        # if info.context.user.is_verified is False and info.context.user.is_moderator is False:
        #     raise GraphQLError("You are not authorized to perform this action")

        new_article = Article(title="Untitled")
        new_article.save()

        creator_byline = ArticleByline(user=info.context.user, article=new_article, is_confirmed=True)
        creator_byline.save()

        return CreateArticle(article=new_article)


class UpdateArticle(graphene.Mutation):
    article = graphene.Field(ArticleType)

    class Arguments:
        id = graphene.String(required=True)
        title = graphene.String()
        seo_title = graphene.String()
        preview_text = graphene.String()
        body = graphene.String()
        is_full_bleed = graphene.Boolean()
        is_excerpt = graphene.Boolean()
        featured_image = ImageInput()
        related_publish_date = graphene.String()
        authors = graphene.List(UserInput)
        content_rating = graphene.String()
        length = graphene.String()
        language = graphene.List(NameWithPriorityInput)
        format = graphene.List(NameWithPriorityInput)
        distribution = graphene.List(graphene.String)
        genre = graphene.List(NameWithPriorityInput)
        countries_represented = graphene.List(NameWithPriorityInput)
        identities_represented = graphene.List(NameWithPriorityInput)
        tag = graphene.List(NameWithPriorityInput)
        price = PriceInput()
        publish_status = graphene.String()
        featured_image_full_bleed_fit = graphene.String()
        featured_image_full_bleed_alignment = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        id = kwargs.get('id')
        title = kwargs.get('title')
        seo_title = kwargs.get('seo_title')
        is_full_bleed = kwargs.get('is_full_bleed')
        is_excerpt = kwargs.get('is_excerpt')
        featured_image = kwargs.get('featured_image')
        preview_text = kwargs.get('preview_text')
        body = kwargs.get('body')
        related_publish_date = kwargs.get('related_publish_date')
        authors = kwargs.get('authors')
        content_rating = kwargs.get('content_rating')
        length = kwargs.get('length')
        language = kwargs.get('language')
        format = kwargs.get('format')
        distribution = kwargs.get('distribution')
        genre = kwargs.get('genre')
        countries_represented = kwargs.get('countries_represented')
        identities_represented = kwargs.get('identities_represented')
        tag = kwargs.get('tag')
        price = kwargs.get('price')
        publish_status = kwargs.get('publish_status')
        featured_image_full_bleed_fit = kwargs.get('featured_image_full_bleed_fit')
        featured_image_full_bleed_alignment = kwargs.get('featured_image_full_bleed_alignment')

        if Article.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target article does not exist! Please refresh or try again later.")

        target_article = Article.objects.get(id=id)

        if ArticleByline.objects.filter(article=target_article, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this article.")

        # Title #

        if title is not None:
            target_article.title = title

        # SEO Title #

        if seo_title is not None:
            target_article.seo_title = seo_title

        # Preview Text #

        if preview_text is not None:
            target_article.preview_text = preview_text

        # Body #

        if body is not None:
            target_article.body = body

        # Publish Status #

        if publish_status is not None:
            target_article.publish_status = PublishStatus(publish_status)

        # Is Full Bleed #

        if is_full_bleed is not None:
            target_article.is_full_bleed = is_full_bleed

        # Featured Image Full Bleed Fit #

        if featured_image_full_bleed_fit is not None:
            target_article.featured_image_full_bleed_fit = ObjectFit(featured_image_full_bleed_fit)

        # Featured Image Full Bleed Alignment #

        if featured_image_full_bleed_alignment is not None:
            target_article.featured_image_full_bleed_alignment = Alignment(featured_image_full_bleed_alignment)

        # Is Excerpt #

        if is_excerpt is not None:
            target_article.is_excerpt = is_excerpt

        # Cover Image #

        if featured_image is not None:

            if ArticleFeaturedImage.objects.filter(article=target_article).exists() is True:
                current_cover = ArticleFeaturedImage.objects.get(article=target_article)

            else:
                current_cover = ArticleFeaturedImage(article=target_article)
                current_cover.save(skip_callback=True)

            if featured_image.data != '':
                save_image_data_via_model(current_cover, featured_image.data, featured_image.name)

            current_cover.alttext = featured_image.alttext
            current_cover.caption = featured_image.caption
            current_cover.save(skip_callback=True)

        # Publication Date #

        if related_publish_date is not None:
            if related_publish_date == '':
                target_article.related_publish_date = None
            else:
                target_article.related_publish_date = get_date_from_string(related_publish_date + '01')

        # Creators #

        if authors is not None:

            creator_input_valid = False

            for creator in authors:
                if get_user_model().objects.filter(username=creator.username).exists():
                    creator_input_valid = True

            if creator_input_valid:
                existing_creator_bylines = ArticleByline.objects.filter(article=target_article)

                for existing_creator_byline in existing_creator_bylines:
                    delete_existing_byline = True
                    for creator in authors:
                        if get_user_model().objects.filter(username=creator.username).exists() and \
                                existing_creator_byline.user.username == creator.username:
                            delete_existing_byline = False
                    if delete_existing_byline:
                        existing_creator_byline.delete()

                for creator in authors:
                    if get_user_model().objects.filter(username=creator.username).exists():
                        stored_user = get_user_model().objects.get(username=creator.username)
                        if ArticleByline.objects.filter(article=target_article, user=stored_user).exists():
                            creator_byline = ArticleByline.objects.get(article=target_article, user=stored_user)
                            creator_byline.article_priority = creator.priority
                        else:
                            creator_byline = ArticleByline(user=stored_user, article=target_article,
                                                                  article_priority=creator.priority,
                                                                  requester=info.context.user)
                            send_byline_email(info.context.user.display_name, target_article.title, stored_user.email,
                                              'creator')
                        creator_byline.save()
                    else:
                        raise GraphQLError(
                            'Specified user {0} does not exist. Please remove and try again.'.format(creator.username))
            else:
                raise GraphQLError('Unable to process request. Article must contain at least one valid creator.'
                                   ' Please refresh and try again.')


        # Price #

        if getattr(target_article, "price") is not None:
            target_article.price.delete()

        if price is not None:

            if price.price_type == 'free' or price.price_type == 'paid':
                new_price_type = PriceType.objects.get(slug=price.price_type)
                new_price = Price(price_type=new_price_type, amount=price.amount, details=price.details)
                new_price.save()
                target_article.price = new_price

            else:
                raise GraphQLError("Price must be either free or paid")

        # Content Rating #

        if content_rating is not None:

            if ContentRating.objects.filter(slug=content_rating).exists() is False:
                raise GraphQLError("Invalid content rating")

            item_object = ContentRating.objects.get(slug=content_rating)
            target_article.content_rating = item_object

        # Length #

        if length is not None:

            if Length.objects.filter(slug=length).exists() is False:
                raise GraphQLError("Invalid length")

            item_object = Length.objects.get(slug=length)
            target_article.length = item_object

        # Language #

        existing_language = ArticleLanguage.objects.filter(article=target_article)
        existing_language.delete()

        if language is not None:
            for item in language:
                item_slug = slugify(item.name)
                if Language.objects.filter(slug=item_slug).exists() is False:
                    new_model = Language(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Language.objects.get(slug=item_slug)
                new_item_record = ArticleLanguage(article=target_article, language=item_object,
                                                  priority=item.priority)
                new_item_record.save()

        # Format #

        existing_format = ArticleFormat.objects.filter(article=target_article)
        existing_format.delete()

        if format is not None:
            for item in format:
                item_slug = slugify(item.name)
                if Format.objects.filter(slug=item_slug).exists() is False:
                    new_model = Format(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Format.objects.get(slug=item_slug)
                new_item_record = ArticleFormat(article=target_article, format=item_object,
                                                priority=item.priority)
                new_item_record.save()

        # Distribution #

        existing_distribution = ArticleDistributionType.objects.filter(article=target_article)
        existing_distribution.delete()

        if distribution is not None:
            for item in distribution:
                if DistributionType.objects.filter(slug=item).exists() is False:
                    raise GraphQLError("Attempted to save Invalid distribution type")

                item_object = DistributionType.objects.get(slug=item)
                new_item_record = ArticleDistributionType(article=target_article, distribution_type=item_object)
                new_item_record.save()

        # Genre #

        existing_genre = ArticleGenre.objects.filter(article=target_article)
        existing_genre.delete()

        if genre is not None:
            for item in genre:
                item_slug = slugify(item.name)
                if Genre.objects.filter(slug=item_slug).exists() is False:
                    new_model = Genre(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Genre.objects.get(slug=item_slug)
                new_item_record = ArticleGenre(article=target_article, genre=item_object,
                                               priority=item.priority)
                new_item_record.save()

        # Countries Represented #

        existing_countries_represented = ArticleCountryRepresented.objects.filter(article=target_article)
        existing_countries_represented.delete()

        if countries_represented is not None:
            for item in countries_represented:
                item_slug = slugify(item.name)
                if Country.objects.filter(slug=item_slug).exists() is False:
                    new_country = Country(name=item.name.capitalize(), slug=item_slug)
                    new_country.save()

                item_object = Country.objects.get(slug=item_slug)
                new_item_record = ArticleCountryRepresented(article=target_article, country=item_object,
                                                            priority=item.priority)
                new_item_record.save()

        # Identities Represented #

        existing_identities_represented = ArticleIdentityRepresented.objects.filter(article=target_article)
        existing_identities_represented.delete()

        if identities_represented is not None:
            for item in identities_represented:
                item_slug = slugify(item.name)
                if Identity.objects.filter(slug=item_slug).exists() is False:
                    new_identity = Identity(name=capitalize_string(item.name), slug=item_slug)
                    new_identity.save()

                item_object = Identity.objects.get(slug=item_slug)
                new_item_record = ArticleIdentityRepresented(article=target_article, identity=item_object,
                                                             priority=item.priority)
                new_item_record.save()

        # Tag #

        existing_tag = ArticleTag.objects.filter(article=target_article)
        existing_tag.delete()

        if tag is not None:
            for item in tag:
                item_slug = slugify(item.name)
                if Tag.objects.filter(slug=item_slug).exists() is False:
                    new_model = Tag(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Tag.objects.get(slug=item_slug)
                new_item_record = ArticleTag(article=target_article, tag=item_object,
                                             priority=item.priority)
                new_item_record.save()

        target_article.save()
        return UpdateArticle(article=target_article)


class UploadArticleImage(graphene.Mutation):
    image = graphene.String()

    class Arguments:
        id = graphene.String(required=True)
        image = ImageInput(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        id = kwargs.get('id')
        image = kwargs.get('image')

        if Article.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target article does not exist! Please refresh or try again later.")

        target_article = Article.objects.get(id=id)

        if ArticleByline.objects.filter(article=target_article, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this article.")

        if image is not None:

            if image.data != '':

                image_path = article_image_path_from_model(target_article, image.name)
                image_save = save_image_data(image_path, image.data)

        return UploadArticleImage(image=image_save)


class SaveArticleBody(graphene.Mutation):
    article = graphene.Field(ArticleType)

    class Arguments:
        id = graphene.String(required=True)
        body = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        id = kwargs.get('id')
        body = kwargs.get('body')

        if Article.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target article does not exist! Please refresh or try again later.")

        target_article = Article.objects.get(id=id)

        if ArticleByline.objects.filter(article=target_article, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this article.")

        if body is not None:
            target_article.body = body

        target_article.save()

        return SaveArticleBody(article=target_article)


class DeleteArticle(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, id):

        if Article.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_article = Article.objects.get(id=id)

        if ArticleByline.objects.filter(article=target_article, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this listing.")

        target_article.delete()
        return True


class CMSMutation(graphene.ObjectType):
    create_article = CreateArticle.Field()
    update_article = UpdateArticle.Field()
    upload_article_image = UploadArticleImage.Field()
    save_article_body = SaveArticleBody.Field()
    delete_article = DeleteArticle.Field()