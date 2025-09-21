from django.urls import path, include
from shophubapp import views

urlpatterns = [
    path('logout/', views.logout_action, name='logout'),
    path('list/<int:id>/', views.view_list, name='list'),
    path('list/<int:list_id>/add-collaborator/', views.add_collaborator, name='add_collaborator'),
    path('notifications/accept/<int:notification_id>/', views.accept_collaboration, name='accept_collaboration'),\
    path('notifications/decline/<int:notification_id>/', views.decline_collaboration, name='decline_collaboration'),
    path('explore/', views.view_explore, name='explore'),
    path('create_list/', views.create_list, name="create_list"),
    path('delete_list/<int:list_id>/', views.delete_list, name='delete_list'),
    path('notifications/', views.notifications, name = 'notifications'),
    path('star_list/<int:list_id>/', views.star_list, name='star_list'),
    path('remove_star_list/<int:list_id>/', views.remove_star_list, name='remove_star_list'),
    path('follower/', views.follower_action, name='follower'),
    path('profile/', views.profile_action, name='profile'),
    path('other_profile/<int:user_id>/',
         views.other_profile_action, name='other_profile'),
    path('get_products/<int:list_id>/', views.get_products, name='get_products'),
    path('get_lists/', views.get_lists, name='get_lists'),
    path('get_all_lists/', views.get_all_lists, name='get_all_lists'),
    path('delete-item/<int:item_id>', views.delete_item, name='delete-item'),
    path('track-click/', views.track_click, name='track_click'),

    path('search-profiles/', views.search_profiles, name='search_profiles'),
    path('send-friend-requests/<str:to_friend>/', views.send_friend_requests, name='send_friend_requests'),

    path('get-friend-requests/', views.get_friend_requests, name='get_friend_requests'),
    path('get-sent-requests/', views.get_sent_requests, name='get_sent_requests'),
    path('accept-friend-requests/<str:to_friend>/',
         views.accept_request, name='accept_requests'),
    path('get-friend-list/', views.get_friend_list, name='get_friend_list'),
    path('send-friend-requests/<str:to_friend>/',
         views.send_friend_requests, name='send_friend_requests'),
     
    path('decline-friend-requests/<str:to_friend>/', views.decline_request, name='decline_requests'),
    path('unfriend/<str:to_friend>/', views.unfriend_action, name='unfriend'),
    path('is_friend_url/<str:to_friend>/', views.is_friend_action, name='is_friend'),
    path('withdraw/<str:to_friend>/', views.withdraw_request, name='withdraw'),


]
