import math
import os
import platform
import subprocess
from lights_off import speak
from lights_off import sound
from lights_off import utils
from . import chooser, main, tweet, view
from lights_off import timeline
from lights_off import globals
from mastodon import MastodonError
def reply(account,status):
	NewTweet=tweet.TweetGui(account,"",type="reply",status=status)
	NewTweet.Show()

def quote(account,status):
	NewTweet=tweet.TweetGui(account,type="quote",status=status)
	NewTweet.Show()

def user_timeline(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"User Timeline","Choose user timeline",u2,"userTimeline")

def user_profile(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"User Profile","Choose user profile",u2,"profile")

def url_chooser(account,status):
	title="Open URL"
	prompt="Select a URL?"
	type=chooser.ChooseGui.TYPE_URL
	urlList=utils.find_urls_in_tweet(status)
	if len(urlList) == 1 and globals.prefs.autoOpenSingleURL:
		utils.openURL(urlList[0])
	else:
		chooser.chooser(account,title,prompt,urlList,type)

def follow(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Follow User","Follow who?",u2,"follow")

def follow_user(account,username):
	try:
		user=account.follow(username)
		sound.play(globals.currentAccount,"follow")
	except MastodonError as error:
		utils.handle_error(error,"Follow "+username)

def unfollow(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Unfollow User","Unfollow who?",u2,"unfollow")

def unfollow_user(account,username):
	try:
		user=account.unfollow(username)
		sound.play(globals.currentAccount,"unfollow")
	except MastodonError as error:
		utils.handle_error(error,"Unfollow "+username)

def block(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Block User","Block who?",u2,"block")

def unblock(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Unblock User","Unblock who?",u2,"block")

def mute(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Mute User","Mute who?",u2,"mute")

def unmute(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Unmute User","Unmute who?",u2,"unmute")

def add_to_list(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Add user to list","Add who?",u2,"list")

def remove_from_list(account,status):
	u=utils.get_user_objects_in_tweet(account,status)
	u2=[]
	for i in u:
		u2.append(i.acct)
	chooser.chooser(account,"Remove user from list","Remove who?",u2,"listr")

def message(account,status):
	# status may be a conversation object (has last_status) or a plain status
	if hasattr(status, "last_status") and status.last_status is not None:
		inner = status.last_status
	else:
		inner = status
	# reply to the other participant, not ourselves
	if inner.account.id == account.me.id:
		others = [a.acct for a in getattr(status, "accounts", []) if a.id != account.me.id]
		user = others[0] if others else inner.account.acct
	else:
		user = inner.account.acct
	message_user(account, user)

def message_user(account,user):
	NewTweet=tweet.TweetGui(account,user,"message")
	NewTweet.Show()

def retweet(account,status):
	try:
		account.retweet(status.id)
		globals.prefs.retweets_sent+=1
		sound.play(globals.currentAccount,"send_boost")
	except MastodonError as error:
		utils.handle_error(error,"retweet")

def like(account,status):
	try:
		status=utils.ensure_attr_access(status)
		if getattr(status,"favourited",False):
			account.unlike(status.id)
			status.favourited=False
			sound.play(globals.currentAccount,"unlike")
		else:
			account.like(status.id)
			globals.prefs.likes_sent+=1
			status.favourited=True
			sound.play(globals.currentAccount,"like")
	except MastodonError as error:
		utils.handle_error(error,"like tweet")

def followers(account,id=-1):
	if id==-1:
		id=account.me.id
	flw=view.UserViewGui(account,account.followers(id=id),"Followers")
	flw.Show()

def friends(account,id=-1):
	if id==-1:
		id=account.me.id
	flw=view.UserViewGui(account,account.friends(id=id),"Friends")
	flw.Show()

def mutual_following(account):
	flw=view.UserViewGui(account,account.mutual_following(),"Mutual followers")
	flw.Show()

def not_following_me(account):
	flw=view.UserViewGui(account,account.not_following_me(),"Users not following me")
	flw.Show()

def not_following(account):
	flw=view.UserViewGui(account,account.not_following(),"users I don't follow")
	flw.Show()

def havent_tweeted(account):
	flw=view.UserViewGui(account,account.havent_posted(),"users who haven't posted recently")
	flw.Show()

def user_timeline_user(account,username,focus=True):
	if username in account.prefs.user_timelines and focus:
		utils.alert("You already have a timeline for this user open.","Error")
		return False
	if len(account.prefs.user_timelines)>=8:
		utils.alert("You cannot have this many user timelines open! Please consider using a list instead.","Error")
		return False
	user=utils.lookup_user_name(account,username)
	if user!=-1:
		if not focus:
			account.timelines.append(timeline.timeline(account,name=username+"'s Timeline",type="user",data=username,user=user,silent=True))
		else:
			account.timelines.append(timeline.timeline(account,name=username+"'s Timeline",type="user",data=username,user=user))
		if username not in account.prefs.user_timelines:
			account.prefs.user_timelines.append(username)
		main.window.refreshTimelines()
		if focus:
			account.currentIndex=len(account.timelines)-1
			main.window.list.SetSelection(len(account.timelines)-1)
			main.window.on_list_change(None)
		return True

def search(account,q,focus=True):
	if not focus:
		account.timelines.append(timeline.timeline(account,name=q+" Search",type="search",data=q,silent=True))
	else:
		account.timelines.append(timeline.timeline(account,name=q+" Search",type="search",data=q))
	if q not in account.prefs.search_timelines:
		account.prefs.search_timelines.append(q)
	main.window.refreshTimelines()
	if focus:
		account.currentIndex=len(account.timelines)-1
		main.window.list.SetSelection(len(account.timelines)-1)
		main.window.on_list_change(None)

def user_search(account,q):
	users=account.api.account_search(q,limit=40)
	u=view.UserViewGui(account,users,"User search for "+q)
	u.Show()

def list_timeline(account,n, q,focus=True):
	if q in account.prefs.list_timelines and focus:
		utils.alert("You already have a timeline for this list open!","Error")
		return
	if len(account.prefs.list_timelines)>=8:
		utils.alert("You cannot have this many list timelines open!","Error")
		return
	if not focus:
		account.timelines.append(timeline.timeline(account,name=n+" List",type="list",data=q,silent=True))
	else:
		account.timelines.append(timeline.timeline(account,name=n+" List",type="list",data=q))
	if q not in account.prefs.list_timelines:
		account.prefs.list_timelines.append(q)
	main.window.refreshTimelines()
	if focus:
		account.currentIndex=len(account.timelines)-1
		main.window.list.SetSelection(len(account.timelines)-1)
		main.window.on_list_change(None)

def next_in_thread(account):
	status=account.currentTimeline.statuses[account.currentTimeline.index]
	reply_to=getattr(status,"in_reply_to_id",None)
	if reply_to is not None:
		newindex=utils.find_status(account.currentTimeline,reply_to)
		if newindex>-1:
			account.currentTimeline.index=newindex
			main.window.list2.SetSelection(newindex)
			return
	sound.play(account,"boundary")

def previous_in_thread(account):
	newindex=utils.find_reply(account.currentTimeline,account.currentTimeline.statuses[account.currentTimeline.index].id)
	if newindex>-1:
		account.currentTimeline.index=newindex
		main.window.list2.SetSelection(newindex)
	else:
		sound.play(account,"boundary")

def previous_from_user(account):
	newindex=-1
	oldindex=account.currentTimeline.index
	user=account.currentTimeline.statuses[account.currentTimeline.index].account
	newindex2=0
	for i in account.currentTimeline.statuses:
		if newindex2>=oldindex:
			break
		if i.account.id==user.id:
			newindex=newindex2
		newindex2+=1

	if newindex>-1:
		account.currentTimeline.index=newindex
		main.window.list2.SetSelection(newindex)
	else:
		sound.play(account,"boundary")

def next_from_user(account):
	newindex=-1
	oldindex=account.currentTimeline.index
	status=account.currentTimeline.statuses[account.currentTimeline.index]
	user=account.currentTimeline.statuses[account.currentTimeline.index].account
	newindex2=0
	for i in account.currentTimeline.statuses:
		if i!=status and i.account.id==user.id and newindex2>=oldindex:
			newindex=newindex2
			break
		newindex2+=1

	if newindex>-1:
		account.currentTimeline.index=newindex
		main.window.list2.SetSelection(newindex)
	else:
		sound.play(account,"boundary")

def delete(account,status):
	try:
		account.api.status_delete(status.id)
		account.currentTimeline.statuses.remove(status)
		main.window.list2.Delete(account.currentTimeline.index)
		sound.play(globals.currentAccount,"delete")
		main.window.list2.SetSelection(account.currentTimeline.index)
	except MastodonError as error:
		utils.handle_error(error,"Delete post")

def load_conversation(account,status):
	for i in account.timelines:
		if i.type=="conversation":
			return False
	account.timelines.append(timeline.timeline(account,name="Conversation with "+status.account.acct,type="conversation",data=status.account.acct,status=status))
	main.window.refreshTimelines()
	main.window.list.SetSelection(len(account.timelines)-1)
	account.currentIndex=len(account.timelines)-1
	main.window.on_list_change(None)

def play(status):
	urls=utils.find_urls_in_tweet(status)
	media=sound.get_media_urls(urls)
	if not media:
		speak.speak("No audio.")
		return
	url=media[0]['url']
	speak.speak("Opening media...")
	import webbrowser
	webbrowser.open(url)

def play_external(status):
	urls=utils.find_urls_in_tweet(status)
	media=sound.get_media_urls(urls)
	if not media:
		speak.speak("No audio.")
		return
	url=media[0]['url']
	speak.speak("Opening media...")
	if globals.prefs.media_player and os.path.exists(globals.prefs.media_player):
		if platform.system()!="Darwin":
			subprocess.Popen([globals.prefs.media_player, url])
		else:
			os.system("open -a "+globals.prefs.media_player+" --args "+url)
	else:
		import webbrowser
		webbrowser.open(url)
