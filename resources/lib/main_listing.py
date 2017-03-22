# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib
import json

import re


import os,sys

from default import addon, addon_path, itemsPerPage, urlMain, subredditsFile, int_CommentTreshold
from default import pluginhandle, WINDOW, forceViewMode, viewMode, comments_viewMode, album_viewMode, autoplayAll, autoplayUnwatched, TitleAddtlInfo, DoNotResolveLinks
from utils import xbmc_busy, log, translation, addDir, addDirR
from reddit import reddit_request

default_frontpage    = addon.getSetting("default_frontpage")
no_index_page        = addon.getSetting("no_index_page") == "true"
main_gui_skin        = addon.getSetting("main_gui_skin")

cxm_show_comment_link     = addon.getSetting("cxm_show_comment_link") == "true"
cxm_show_comments         = addon.getSetting("cxm_show_comments") == "true"
cxm_show_go_to            = addon.getSetting("cxm_show_go_to") == "true"
cxm_show_new_from         = addon.getSetting("cxm_show_new_from") == "true"
cxm_show_add_shortcuts    = addon.getSetting("cxm_show_add_shortcuts") == "true"
cxm_show_filter_subreddit = addon.getSetting("cxm_show_filter_subreddit") == "true"
cxm_show_filter_domain    = addon.getSetting("cxm_show_filter_domain") == "true"
cxm_show_open_browser     = addon.getSetting("cxm_show_open_browser") == "true"


def index(url,name,type):
    from utils import xstr, samealphabetic, hassamealphabetic
    from reddit import load_subredditsFile, parse_subreddit_entry, create_default_subreddits, assemble_reddit_filter_string, ret_sub_info

    ## this is where the main screen is created
    content = ""
    if not os.path.exists(subredditsFile):  #if not os.path.exists(subredditsFile):
        create_default_subreddits()

    #if os.path.exists(subredditsPickle):
    #    subreddits_dlist=load_dict(subredditsPickle)
    #log( pprint.pformat(subreddits_dlist, indent=1) )
    #for e in subreddits_dlist: log(e.get('entry_name'))

    #testing code
    #h="as asd [S]asdasd[/S] asdas "
    #log(markdown_to_bbcode(h))
    #addDir('test', "url", "next_mode", "", "subreddit" )

    #liz = xbmcgui.ListItem(label="test", label2="label2", iconImage="DefaultFolder.png")
    #u=sys.argv[0]+"?url=&mode=callwebviewer&type="
    #xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=False)

    #liz = xbmcgui.ListItem().fromString('Hello World')
    #xbmcplugin.addDirectoryItem(handle=pluginhandle, listitem=liz, isFolder=False)
    subredditsFile_entries=load_subredditsFile()

    subredditsFile_entries.sort(key=lambda y: y.lower())

    addtl_subr_info={}

    #this controls what infolabels will be used by the skin. very skin specific.
    #  for estuary, this lets infolabel:plot (and genre) show up below the folder
    #  giving us the opportunity to provide a shortcut_description about the shortcuts
    xbmcplugin.setContent(pluginhandle, "mixed") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos

    next_mode='listSubReddit'

    for subreddit_entry in subredditsFile_entries:
        #strip out the alias identifier from the subreddit string retrieved from the file so we can process it.
        #subreddit, alias = subreddit_alias(subreddit_entry)
        addtl_subr_info=ret_sub_info(subreddit_entry)

        entry_type, subreddit, alias, shortcut_description=parse_subreddit_entry(subreddit_entry)
        #log( subreddit + "   " + shortcut_description )

        #url= urlMain+"/r/"+subreddit+"/.json?"+nsfw+allHosterQuery+"&limit="+itemsPerPage
        url= assemble_reddit_filter_string("",subreddit, "yes")
        #log("assembled================="+url)
        if subreddit.lower() == "all":
            addDir(subreddit, url, next_mode, "", subreddit, { "plot": translation(30009) } )  #Displays the currently most popular content from all of reddit....
        else:
            if addtl_subr_info: #if we have additional info about this subreddit
                title=addtl_subr_info.get('title')+'\n'
                display_name=xstr(addtl_subr_info.get('display_name'))
                if samealphabetic( title, display_name): title=''
                #if re.sub('\W+','', display_name.lower() )==re.sub('\W+','', title.lower()): title=''
                #display_name=re.sub('\W+','', display_name.lower() )
                #title=re.sub('\W+','', title.lower())

                header_title=xstr(addtl_subr_info.get('header_title'))
                public_description=xstr( addtl_subr_info.get('public_description'))

                if samealphabetic( header_title, public_description): public_description=''
                if samealphabetic(title,public_description): public_description=''
                #if hassamealphabetic(header_title,title,public_description): public_description=''

                shortcut_description='[COLOR cadetblue][B]r/%s[/B][/COLOR]\n%s[I]%s[/I]\n%s' %(display_name,title,header_title,public_description )

                icon=addtl_subr_info.get('icon_img')
                banner=addtl_subr_info.get('banner_img')
                header=addtl_subr_info.get('header_img')  #usually the small icon on upper left side on subreddit screen

                #log( subreddit + ' icon=' + repr(icon) +' header=' + repr(header))
                #picks the first item that is not None
                icon=next((item for item in [icon,banner,header] if item ), '')

                addDirR(alias, url, next_mode, icon,
                        type=subreddit,
                        listitem_infolabel={ "plot": shortcut_description },
                        file_entry=subreddit_entry,
                        banner_image=banner )
            else:
                addDirR(alias, url, next_mode, "", subreddit, { "plot": shortcut_description }, subreddit_entry )

    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSubreddit', "", "", { "plot": translation(30006) } ) #"Customize this list with your favorite subreddit."
    addDir("[B]- "+translation(30005)+"[/B]", "",'searchReddits', "", "", { "plot": translation(30010) } ) #"Search reddit for a particular post or topic

    xbmcplugin.endOfDirectory(pluginhandle)

def listSubReddit(url, name, subreddit_key):
    import datetime
    from utils import unescape, strip_emoji, pretty_datediff, post_is_filtered_out, clean_str
    from reddit import determine_if_video_media_from_reddit_json, ret_sub_icon, has_multiple_subreddits
    #url=r'https://www.reddit.com/r/videos/search.json?q=nsfw:yes+site%3Ayoutu.be+OR+site%3Ayoutube.com+OR+site%3Avimeo.com+OR+site%3Aliveleak.com+OR+site%3Adailymotion.com+OR+site%3Agfycat.com&sort=relevance&restrict_sr=on&limit=5&t=week'
    #url='https://www.reddit.com/search.json?q=site%3Adailymotion&restrict_sr=&sort=relevance&t=week'

    show_listVideos_debug=True
    credate = ""
    is_a_video=False
    title_line2=""
    log("listSubReddit subreddit=%s url=%s" %(subreddit_key,url) )
    t_on = translation(30071)  #"on"
    #t_pts = u"\U0001F4AC"  # translation(30072) #"cmnts"  comment bubble symbol. doesn't work
    #t_pts = u"\U00002709"  # translation(30072)   envelope symbol
    t_pts='c'

    thumb_w=0
    thumb_h=0

    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "movies") #files, songs, artists, albums, movies, tvshows, episodes, musicvideos

    dialog_progress = xbmcgui.DialogProgressBG()
    dialog_progress_heading='Loading'
    dialog_progress.create(dialog_progress_heading )
    dialog_progress.update(0,dialog_progress_heading, subreddit_key  )

    content = reddit_request(url)

    if not content:
        return

    page_title="[COLOR cadetblue]%s[/COLOR]" %subreddit_key

    #setPluginCategory lets us show text at the top of window, we take advantage of this and put the subreddit name
    xbmcplugin.setPluginCategory(pluginhandle, page_title)

    info_label={ "plot": translation(30013) }  #Automatically play videos
    if autoplayAll:       addDir("[B]- "+translation(30016)+"[/B]", url, 'autoPlay', "", "ALL", info_label)
    if autoplayUnwatched: addDir("[B]- "+translation(30017)+"[/B]" , url, 'autoPlay', "", "UNWATCHED", info_label)

    #7-15-2016  removed the "replace(..." statement below cause it was causing error
    #content = json.loads(content.replace('\\"', '\''))
    content = json.loads(content)

    #log("query returned %d items " % len(content['data']['children']) )
    posts_count=len(content['data']['children'])

    hms = has_multiple_subreddits(content['data']['children'])

    for idx, entry in enumerate(content['data']['children']):
        try:
            #on 3/21/2017 we're adding a new feature that lets users view their saved posts by entering /user/username/saved as their subreddit.
            #  in addition to saved posts, users can also save comments. we need to handle it by checking for "kind"
            kind=entry.get('kind')  #t1 for comments  t3 for posts
            data=entry.get('data')
            if post_is_filtered_out( data ):
                continue

            if kind=='t3':
                title = clean_str(data,['title'])
                description=clean_str(data,['media','oembed','description'])
                post_selftext=clean_str(data,['selftext'])

                description=post_selftext+'[CR]'+description if post_selftext else description
            else:
                title=clean_str(data,['link_title'])
                description=clean_str(data,['body'])

            title = strip_emoji(title) #an emoji in the title was causing a KeyError  u'\ud83c'

            commentsUrl = urlMain+clean_str(data,['permalink'])
            #if show_listVideos_debug :log("commentsUrl"+str(idx)+"="+commentsUrl)

            try:
                aaa = data.get('created_utc')
                credate = datetime.datetime.utcfromtimestamp( aaa )
                now_utc = datetime.datetime.utcnow()
                pretty_date=pretty_datediff(now_utc, credate)
                credate = str(credate)
            except (AttributeError,TypeError,ValueError):
                credate = ""

            subreddit=clean_str(data,['subreddit'])
            author=clean_str(data,['author'])
            domain=clean_str(data,['domain'])
            #log("     DOMAIN%.2d=%s" %(idx,domain))

            #ups = data.get('score',0)       #downs not used anymore
            num_comments = data.get('num_comments',0)
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts  |  "+str(comments)+" cmnts  |  by "+author+"[/I]\n"+description
            #description = "[COLOR blue]r/"+ subreddit + "[/COLOR]  [I]" + str(ups)+" pts.  |  by "+author+"[/I]\n"+description
            #description = title_line2+"\n"+description
            #if show_listVideos_debug :log("DESCRIPTION"+str(idx)+"=["+description+"]")
            d_url=clean_str(data,['url'])
            link_url=clean_str(data,['link_url'])
            media_oembed_url=clean_str(data,['media','oembed','url'])

            media_url=next((item for item in [d_url,link_url,media_oembed_url] if item ), '')
            #log("          url"+str(idx)+"="+media_url)

            thumb=clean_str(data,['thumbnail'])
            #if show_listSubReddit_debug : log("       THUMB%.2d=%s" %( idx, thumb ))

            if thumb in ['nsfw','default','self']:  #reddit has a "default" thumbnail (alien holding camera with "?")
                thumb=""

            if thumb=="":
                thumb=clean_str(data,['media','oembed','thumbnail_url']).replace('&amp;','&')

            if thumb=="":  #use this subreddit's icon if thumb still empty
                try: thumb=ret_sub_icon(subreddit)
                except: pass

            try:
                #collect_thumbs(entry)
                preview=data.get('preview')['images'][0]['source']['url'].encode('utf-8').replace('&amp;','&')
                #poster = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
                #t=thumb.split('?')[0]
                #can't preview gif thumbnail on thumbnail view, use alternate provided by reddit
                #if t.endswith('.gif'):
                    #log('  thumb ends with .gif')
                #    thumb = entry['data']['thumbnail'].encode('utf-8')
                try:
                    thumb_h = float( data.get('preview')['images'][0]['source']['height'] )
                    thumb_w = float( data.get('preview')['images'][0]['source']['width'] )
                except (AttributeError,TypeError,ValueError):
                    thumb_w=0; thumb_h=0

            except Exception as e:
                #log("   getting preview image EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
                thumb_w=0; thumb_h=0; preview="" #a blank preview image will be replaced with poster_url from make_addon_url_from() for domains that support it

            is_a_video = determine_if_video_media_from_reddit_json(data)

            over_18=data.get('over_18')

            #setting: toggle showing 2-line title
            #log("   TitleAddtlInfo "+str(idx)+"="+str(TitleAddtlInfo))
            title_line2=""
            #if TitleAddtlInfo:
            #title_line2 = "[I][COLOR dimgrey]%s by %s [COLOR darkslategrey]r/%s[/COLOR] %d pts.[/COLOR][/I]" %(pretty_date,author,subreddit,ups)
            #title_line2 = "[I][COLOR dimgrey]"+pretty_date+" by "+author+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"

            title_line2 = "[I][COLOR dimgrey]%s %s [COLOR cadetblue]r/%s[/COLOR] (%d) %s[/COLOR][/I]" %(pretty_date,t_on, subreddit,num_comments, t_pts)
            #title_line2 = "[I]"+str(idx)+". [COLOR dimgrey]"+ media_url[0:50]  +"[/COLOR][/I] "  # +"    "+" [COLOR darkslategrey]r/"+subreddit+"[/COLOR] "+str(ups)+" pts.[/COLOR][/I]"

            #if show_listVideos_debug : log( ("v" if is_a_video else " ") +"     TITLE"+str(idx)+"="+title)
            if show_listVideos_debug : log("  POST%cTITLE%.2d=%s" %( ("v" if is_a_video else " "), idx, title ))
            #if show_listVideos_debug :log("      OVER_18"+str(idx)+"="+str(over_18))
            #if show_listVideos_debug :log("   IS_A_VIDEO"+str(idx)+"="+str(is_a_video))
            #if show_listVideos_debug :log("        THUMB"+str(idx)+"="+thumb)
            #if show_listVideos_debug :log("    MediaURL%.2d=%s" % (idx,media_url) )

            #if show_listVideos_debug :log("       HOSTER"+str(idx)+"="+hoster)
            #log("    VIDEOID"+str(idx)+"="+videoID)
            #log( "["+description+"]1["+ str(date)+"]2["+ str( count)+"]3["+ str( commentsUrl)+"]4["+ str( subreddit)+"]5["+ video_url +"]6["+ str( over_18))+"]"

            loading_percentage=int((float(idx)/posts_count)*100)
            dialog_progress.update( loading_percentage,dialog_progress_heading, title  )

            addLink(title=title,
                    title_line2=title_line2,
                    iconimage=thumb,
                    previewimage=preview,
                    preview_w=thumb_w,
                    preview_h=thumb_h,
                    domain=domain,
                    description=description,
                    credate=credate,
                    reddit_says_is_video=is_a_video,
                    commentsUrl=commentsUrl,
                    subreddit=subreddit,
                    media_url=media_url,
                    over_18=over_18,
                    posted_by=author,
                    num_comments=num_comments,
                    post_index=idx,
                    post_total=posts_count,
                    many_subreddit=hms)
        except Exception as e:
            log(" EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
            pass

    #log("**reddit query returned "+ str(idx) +" items")
    #window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    #log("focusid:"+str(window.getFocusId()))
    dialog_progress.update( 100,dialog_progress_heading  )
    dialog_progress.close() #it is important to close xbmcgui.DialogProgressBG

    try:
        #this part makes sure that you load the next page instead of just the first
        after=""
        after = content['data']['after']
        if "&after=" in currentUrl:
            nextUrl = currentUrl[:currentUrl.find("&after=")]+"&after="+after
        else:
            nextUrl = currentUrl+"&after="+after

        # plot shows up on estuary. etc. ( avoids the "No information available" message on description )
        info_label={ "plot": translation(30004) + '[CR]' + page_title}
        addDir(translation(30004), nextUrl, 'listSubReddit', "", subreddit_key,info_label)   #Next Page
        #if show_listVideos_debug :log("NEXT PAGE="+nextUrl)
    except:
        pass

    #the +'s got removed by url conversion
    subreddit_key=subreddit_key.replace(' ','+')
    viewID=WINDOW.getProperty( "viewid-"+subreddit_key )
    #log("  custom viewid %s for %s " %(viewID,subreddit_key) )

    if viewID:
        log("  custom viewid %s for %s " %(viewID,subreddit_key) )
        xbmc.executebuiltin('Container.SetViewMode(%s)' %viewID )
    else:
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

    xbmcplugin.endOfDirectory(handle=pluginhandle,
                              succeeded=True,
                              updateListing=False,   #setting this to True causes the ".." entry to quit the plugin
                              cacheToDisc=True)

def addLink(title, title_line2, iconimage, previewimage,preview_w,preview_h,domain,description, credate, reddit_says_is_video, commentsUrl, subreddit, media_url, over_18, posted_by="", num_comments=0,post_index=1,post_total=1,many_subreddit=False ):
    from domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type

    post_title=title
    il_description=""
    n=""  #will hold red nsfw asterisk string
    isFolder=True
    thumb_url=''

    h="[B]" + domain + "[/B]: "
    if over_18:
        mpaa="R"
        n = "[COLOR red]*[/COLOR] "
        #description = "[B]" + hoster + "[/B]:[COLOR red][NSFW][/COLOR] "+title+"\n" + description
        il_description = "[COLOR red][NSFW][/COLOR] "+ h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"
    else:
        mpaa=""
        n=""
        il_description = h+title+"[CR]" + "[COLOR grey]" + description + "[/COLOR]"

    if TitleAddtlInfo:     #put the additional info on the description if setting set to single line titles
        log( repr(title_line2 ))
        post_title=n+title+"[CR]"+title_line2
    else:
        post_title=n+title
        il_description=title_line2+"[CR]"+il_description

    il={"title": post_title, "plot": il_description, "plotoutline": il_description, "Aired": credate, "mpaa": mpaa, "Genre": "r/"+subreddit, "studio": domain, "director": posted_by }   #, "duration": 1271}   (duration uses seconds for titan skin

    liz=xbmcgui.ListItem(label=post_title)

    #this is a video plugin, set type to video so that infolabels show up.
    liz.setInfo(type='video', infoLabels=il)

    if iconimage in ["","nsfw", "default"]:
        #log( title+ ' iconimage blank['+iconimage+']['+thumb_url+ ']media_url:'+media_url )
        iconimage=thumb_url

    preview_ar=0.0
    if (preview_w==0 or preview_h==0) != True:
        preview_ar=float(preview_w) / preview_h
        #log("preview ar: "+ repr(preview_ar))

    if previewimage: needs_preview=False
    else:            needs_preview=True  #reddit has no thumbnail for this link. please get one

    #DirectoryItem_url=sys.argv[0]+"?url="+ urllib.quote_plus(media_url) +"&mode=play"

    if DoNotResolveLinks:
        ld=None
        DirectoryItem_url=sys.argv[0]\
            +"?url="+ urllib.quote_plus(media_url) \
            +"&name="+urllib.quote_plus(title) \
            +"&mode=play"
        setProperty_IsPlayable='true'
        isFolder=False
        title_prefix=''
    else:
        ld=parse_reddit_link(media_url,reddit_says_is_video, needs_preview, False, preview_ar  )

        if needs_preview and ld:
            queried_preview_image= next((i for i in [ld.poster,ld.thumb] if i ), '')
            previewimage=queried_preview_image

        arg_name=title
        arg_type=previewimage
        if ld:
            #log('    ' + ld.media_type + ' -> ' + ld.link_action )
            #log('    ***icon:' + ld.thumb + ' -> ' + ld.link_action )
            if iconimage in ["","nsfw", "default"]: iconimage=ld.thumb

        DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld,
                                                                                                                        media_url,
                                                                                                                        arg_name,
                                                                                                                        arg_type,
                                                                                                                        script_to_call="",
                                                                                                                        on_autoplay=False,
                                                                                                                        img_w=preview_w,
                                                                                                                        img_h=preview_h)
    if title_prefix:
        liz.setLabel( title_prefix+' '+post_title )

    liz.setProperty('IsPlayable', setProperty_IsPlayable)
    liz.setInfo('video', {"title": liz.getLabel(), } )

    liz.setArt({"thumb": iconimage, "poster":previewimage, "banner":iconimage, "fanart":previewimage, "landscape":previewimage, })
    entries = build_context_menu_entries(num_comments, commentsUrl, many_subreddit, subreddit, domain, media_url) #entries for listbox for when you type 'c' or rt-click

    liz.addContextMenuItems(entries)
    #log( 'playcount=' + repr(getPlayCount(DirectoryItem_url)))
    #log( 'DirectoryItem_url=' + DirectoryItem_url)
    xbmcplugin.addDirectoryItem(pluginhandle, DirectoryItem_url, listitem=liz, isFolder=isFolder, totalItems=post_total)

    return

def build_context_menu_entries(num_comments,commentsUrl, many_subreddit, subreddit, domain, link_url):
    from reddit import assemble_reddit_filter_string, subreddit_in_favorites
    from utils import colored_subreddit

    s=(subreddit[:12] + '..') if len(subreddit) > 12 else subreddit     #crop long subreddit names in context menu
    colored_subreddit_short=colored_subreddit( s )
    colored_subreddit_full=colored_subreddit( subreddit )
    colored_domain_full=colored_subreddit( domain, 'tan',False )
    entries=[]

    #sys.argv[0] is plugin://plugin.video.reddit_viewer/
    #prl=zaza is just a dummy: during testing the first argument is ignored... possible bug?

    if cxm_show_open_browser:
            entries.append( ( translation(30509),  #Open in browser
                              "XBMC.RunPlugin(%s?mode=openBrowser&url=%s)" % ( sys.argv[0],  urllib.quote_plus( link_url ) ) ) )

    if cxm_show_comment_link or cxm_show_comments:
        if num_comments > 0:
            #if we are using a custom gui to show comments, we need to use RunPlugin. there is a weird loading/pause if we use XBMC.Container.Update. i think xbmc expects us to use addDirectoryItem
            #  if we have xbmc manage the gui(addDirectoryItem), we need to use XBMC.Container.Update. otherwise we'll get the dreaded "Attempt to use invalid handle -1" error
            #entries.append( ( translation(30050) + " (c)",  #Show comments
            #              "XBMC.RunPlugin(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            #entries.append( ( translation(30052) , #Show comment links
            #              "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            if cxm_show_comment_link:
                entries.append( ( translation(30052) , #Show comment links
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s&type=linksOnly)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            if cxm_show_comments:
                entries.append( ( translation(30050) ,  #Show comments
                                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listLinksInComment&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(commentsUrl) ) ) )
            #entries.append( ( translation(30050) + " (ActivateWindow)",  #Show comments
            #              "XBMC.ActivateWindow(Video, %s?mode=listLinksInComment&url=%s)" % (  sys.argv[0], urllib.quote_plus(site) ) ) )      #***  ActivateWindow is for the standard xbmc window
        else:
            entries.append( ( translation(30053) ,  #No comments
                          "xbmc.executebuiltin('Action(Close)')" ) )

    if many_subreddit and cxm_show_go_to:
        entries.append( ( translation(30051)+" %s" %colored_subreddit_full ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit,True)  ) ) ) )

    if cxm_show_new_from:
        #show check /new from this subreddit if it is all the same subreddit
        entries.append( ( translation(30055)+" %s" %colored_subreddit_short ,
                          "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=listSubReddit&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(assemble_reddit_filter_string("",subreddit+'/new',True)  ) ) ) )

    if cxm_show_add_shortcuts:
        if not subreddit_in_favorites(subreddit):
            #add selected subreddit to shortcuts
            entries.append( ( translation(30056) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addSubreddit&url=%s)" % ( sys.argv[0], subreddit ) ) )

    if cxm_show_filter_subreddit:
            entries.append( ( translation(30057) %colored_subreddit_short ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], subreddit, 'subreddit' ) ) )
    if cxm_show_filter_domain:
            entries.append( ( translation(30057) %colored_domain_full ,
                              "XBMC.RunPlugin(%s?mode=addtoFilter&url=%s&type=%s)" % ( sys.argv[0], domain, 'domain' ) ) )
    #not working...
    #entries.append( ( translation(30054) ,
    #                  "XBMC.Container.Update(%s?path=%s?prl=zaza&mode=playURLResolver&url=%s)" % ( sys.argv[0], sys.argv[0],urllib.quote_plus(media_url) ) ) )
    #entries.append( ( translation(30054) ,
    #                  "XBMC.RunPlugin(%s?path=%s?prl=zaza&mode=playURLRVideo&url=%s)" % ( sys.argv[0], sys.argv[0], urllib.quote_plus(media_url) ) ) )


    #favEntry = '<favourite name="'+title+'" url="'+DirectoryItem_url+'" description="'+description+'" thumb="'+iconimage+'" date="'+credate+'" site="'+site+'" />'
    #entries.append((translation(30022), 'RunPlugin(plugin://'+addonID+'/?mode=addToFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
    return entries



def listLinksInComment(url, name, type):
    from domains import parse_reddit_link, sitesBase, build_DirectoryItem_url_based_on_media_type
    from utils import markdown_to_bbcode, unescape, ret_info_type_icon, build_script
    #from resources.domains import make_addon_url_from
    #called from context menu
    log('listLinksInComment:%s:%s' %(type,url) )

    #does not work for list comments coz key is the playable url (not reddit comments url)
    #msg=WINDOW.getProperty(url)
    #WINDOW.clearProperty( url )
    #log( '   msg=' + msg )

    directory_items=[]
    author=""
    ShowOnlyCommentsWithlink=False

    if type=='linksOnly':
        ShowOnlyCommentsWithlink=True

    #sometimes the url has a query string. we discard it coz we add .json at the end
    #url=url.split('?', 1)[0]+'.json'

    #url='https://www.reddit.com/r/Music/comments/4k02t1/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/' + '.json'
    #only get up to "https://www.reddit.com/r/Music/comments/4k02t1".
    #   do not include                                            "/bonnie_tyler_total_eclipse_of_the_heart_80s_pop/"
    #   because we'll have problem when it looks like this: "https://www.reddit.com/r/Overwatch/comments/4nx91h/ever_get_that_feeling_dÃ©jÃ _vu/"

    #url=re.findall(r'(.*/comments/[A-Za-z0-9]+)',url)[0]
    url=urllib.quote_plus(url,safe=':/')
    url+='.json'

    content = reddit_request(url)
    if not content: return

    content = json.loads(content)

    del harvest[:]
    #harvest links in the post text (just 1)
    r_linkHunter(content[0]['data']['children'])

    try:submitter=content[0]['data']['children'][0]['data']['author']
    except: submitter=''

    #the post title is provided in json, we'll just use that instead of messages from addLink()
    try:post_title=content[0]['data']['children'][0]['data']['title']
    except:post_title=''
    #for i, h in enumerate(harvest):
    #    log("aaaaa first harvest "+h[2])

    #harvest links in the post itself
    r_linkHunter(content[1]['data']['children'])

    comment_score=0
    for i, h in enumerate(harvest):
        try:
            #log(str(i)+"  score:"+ str(h[0]).zfill(5)+" "+ h[1] +'|'+ h[3] )
            comment_score=h[0]
            #log("score %d < %d (%s)" %(comment_score,int_CommentTreshold, CommentTreshold) )
            link_url=h[2]
            desc100=h[3].replace('\n',' ')[0:100] #first 100 characters of description

            kind=h[6] #reddit uses t1 for user comments and t3 for OP text of the post. like a poster describing the post.
            d=h[5]   #depth of the comment

            tab=" "*d if d>0 else "-"

            from urlparse import urlparse
            domain = '{uri.netloc}'.format( uri=urlparse( link_url ) )

            author=h[7]
            DirectoryItem_url=''

            if comment_score < int_CommentTreshold:
                continue

            #hoster, DirectoryItem_url, videoID, mode_type, thumb_url,poster_url, isFolder,setInfo_type, setProperty_IsPlayable =make_addon_url_from(h[2])
            #if link_url:
            #    log( '  comment %s TITLE:%s... link[%s]' % ( str(d).zfill(3), desc100.ljust(20)[:20],link_url ) )

            ld=parse_reddit_link(link_url=link_url, assume_is_video=False, needs_preview=True, get_playable_url=True )

            if kind=='t1':
                list_title=r"[COLOR cadetblue]%3d[/COLOR] %s" %( h[0], tab )
            elif kind=='t3':
                list_title=r"[COLOR cadetblue]Title [/COLOR] %s" %( tab )

            #helps the the textbox control treat [url description] and (url) as separate words. so that they can be separated into 2 lines
            plot=h[3].replace('](', '] (')
            plot= markdown_to_bbcode(plot)
            plot=unescape(plot)  #convert html entities e.g.:(&#39;)

#            liz=xbmcgui.ListItem(label=     "[COLOR greenyellow]*"+     list_title+"[%s] %s"%(domain, result.replace('\n',' ')[0:100])  + "[/COLOR]",
#                                 label2="",
#                                 iconImage="",
#                                 thumbnailImage='',
#                                 path=DirectoryItem_url)

            liz=xbmcgui.ListItem(label=list_title +': '+ desc100)

            liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": plot, "studio": domain, "votes": str(comment_score), "director": author  } )
            isFolder=False

            #force all links to ytdl to see if it can be played
            if link_url:

                DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, link_url)

                liz.setProperty('IsPlayable', setProperty_IsPlayable)
                liz.setProperty('url', DirectoryItem_url)  #<-- needed by the xml gui skin
                liz.setPath(DirectoryItem_url)

                if domain:
                    plot= "  [COLOR greenyellow][%s] %s"%(domain, plot )  + "[/COLOR]"
                else:
                    plot= "  [COLOR greenyellow][%s]"%( plot ) + "[/COLOR]"
                liz.setLabel(list_title+plot)

                #log('      there is a link from %s' %domain)
                if ld:
                    liz.setArt({"thumb": ld.poster, "poster":ld.poster, "banner":ld.poster, "fanart":ld.poster, "landscape":ld.poster   })
                #else:
                #    DirectoryItem_url=sys.argv[0]+"?url="+ urllib.quote_plus(link_url) +"&mode=play"

            if DirectoryItem_url:
                #log( 'IsPlayable:'+setProperty_IsPlayable )
                directory_items.append( (DirectoryItem_url, liz, isFolder,) )
                #xbmcplugin.addDirectoryItem(handle=pluginhandle,url=DirectoryItem_url,listitem=liz,isFolder=isFolder)
            else:
                #this section are for comments that have no links
                if not ShowOnlyCommentsWithlink:
                    result=h[3].replace('](', '] (')
                    result=markdown_to_bbcode(result)
                    liz=xbmcgui.ListItem(label=list_title + desc100)
                    liz.setInfo( type="Video", infoLabels={ "Title": h[1], "plot": result, "studio": domain, "votes": str(h[0]), "director": author } )
                    liz.setProperty('IsPlayable', 'false')

                    directory_items.append( ("", liz, False,) )
                    #xbmcplugin.addDirectoryItem(handle=pluginhandle,url="",listitem=liz,isFolder=False)

                #END section are for comments that have no links or unsupported links
        except Exception as e:
            log('  EXCEPTION:' + str(e) )

        #for di in directory_items:
        #    log( str(di) )

    log('  comments_view id=%s' %comments_viewMode)

    #xbmcplugin.setContent(pluginhandle, "mixed")  #in estuary, mixed have limited view id's available. it has widelist which is nice for comments but we'll just stick with 'movies'
    xbmcplugin.setContent(pluginhandle, "movies")    #files, songs, artists, albums, movies, tvshows, episodes, musicvideos
    xbmcplugin.setPluginCategory(pluginhandle,'Comments')

    xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
    xbmcplugin.endOfDirectory(pluginhandle)

    if comments_viewMode:
        xbmc.executebuiltin('Container.SetViewMode(%s)' %comments_viewMode)


harvest=[]
def r_linkHunter(json_node,d=0):
    #from resources.domains import url_is_supported
    from utils import unescape
    #recursive function to harvest stuff from the reddit comments json reply
    prog = re.compile('<a href=[\'"]?([^\'" >]+)[\'"]>(.*?)</a>')
    for e in json_node:
        link_desc=""
        link_http=""
        author=""
        created_utc=""
        if e['kind']=='t1':     #'t1' for comments   'more' for more comments (not supported)

            #log("replyid:"+str(d)+" "+e['data']['id'])
            body=e['data']['body'].encode('utf-8')

            #log("reply:"+str(d)+" "+body.replace('\n','')[0:80])

            try: replies=e['data']['replies']['data']['children']
            except: replies=""

            try: score=e['data']['score']
            except: score=0

            try: post_text=unescape( e['data']['body'].encode('utf-8') )
            except: post_text=""
            post_text=post_text.replace("\n\n","\n")

            try: post_html=unescape( e['data']['body_html'].encode('utf-8') )
            except: post_html=""

            try: created_utc=e['data']['created_utc']
            except: created_utc=""

            try: author=e['data']['author'].encode('utf-8')
            except: author=""

            #i initially tried to search for [link description](https:www.yhotuve.com/...) in the post_text but some posts do not follow this convention
            #prog = re.compile('\[(.*?)\]\((https?:\/\/.*?)\)')
            #result = prog.findall(post_text)

            result = prog.findall(post_html)
            if result:
                #store the post by itself and then a separate one for each link.
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

                for link_http,link_desc in result:
                    #if url_is_supported(link_http) :
                        #store an entry for every supported link.
                    harvest.append((score, link_desc, link_http, link_desc, post_html, d, "t1",author,created_utc,)   )
            else:
                harvest.append((score, link_desc, link_http, post_text, post_html, d, "t1",author,created_utc,)   )

            d+=1 #d tells us how deep is the comment in
            r_linkHunter(replies,d)
            d-=1

        if e['kind']=='t3':     #'t3' for post text (a description of the post)
            #log(str(e))
            #log("replyid:"+str(d)+" "+e['data']['id'])
            try: score=e['data']['score']
            except: score=0

            try: self_text=unescape( e['data']['selftext'].encode('utf-8') )
            except: self_text=""

            try: self_text_html=unescape( e['data']['selftext_html'].encode('utf-8') )
            except: self_text_html=""

            result = prog.findall(self_text_html)
            if len(result) > 0 :
                harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc, )   )

                for link_http,link_desc in result:
                    harvest.append((score, link_desc, link_http, link_desc, self_text_html, d, "t3",author,created_utc, )   )
            else:
                if len(self_text) > 0: #don't post an empty titles
                    harvest.append((score, link_desc, link_http, self_text, self_text_html, d, "t3",author,created_utc,)   )



if __name__ == '__main__':
    pass