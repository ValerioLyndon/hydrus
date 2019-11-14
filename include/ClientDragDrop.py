from . import ClientGUIFunctions
from . import HydrusGlobals as HG
from . import HydrusPaths
import json
import os
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW
from . import QtPorting as QP

def DoFileExportDragDrop( window, page_key, media, alt_down ):
    
    drop_source = QG.QDrag( window )
    
    data_object = QC.QMimeData()
    
    #
    
    new_options = HG.client_controller.new_options
    
    do_secret_discord_dnd_fix = new_options.GetBoolean( 'secret_discord_dnd_fix' ) and alt_down
    
    #
    
    client_files_manager = HG.client_controller.client_files_manager
    
    original_paths = []
    
    total_size = 0
    
    for m in media:
        
        hash = m.GetHash()
        mime = m.GetMime()
        
        total_size += m.GetSize()
        
        original_path = client_files_manager.GetFilePath( hash, mime, check_file_exists = False )
        
        original_paths.append( original_path )
        
    
    #
    
    discord_dnd_fix_possible = new_options.GetBoolean( 'discord_dnd_fix' ) and len( original_paths ) <= 50 and total_size < 200 * 1048576
    
    temp_dir = HG.client_controller.temp_dir
    
    if do_secret_discord_dnd_fix:
        
        dnd_paths = original_paths
        
        flags = QC.Qt.MoveAction
        
    elif discord_dnd_fix_possible and os.path.exists( temp_dir ):
        
        dnd_paths = []
        
        for original_path in original_paths:
            
            filename = os.path.basename( original_path )
            
            dnd_path = os.path.join( temp_dir, filename )
            
            if not os.path.exists( dnd_path ):
                
                HydrusPaths.MirrorFile( original_path, dnd_path )
                
            
            dnd_paths.append( dnd_path )
            
        
        flags = QC.Qt.MoveAction | QC.Qt.CopyAction
        
    else:
        
        dnd_paths = original_paths
        flags = QC.Qt.CopyAction
        
    
    uri_list = []
    
    for path in dnd_paths:
        
        uri_list.append( QC.QUrl.fromLocalFile( path ) )
        
    
    data_object.setUrls( uri_list )
    
    #
    
    hashes = [ m.GetHash() for m in media ]
    
    if page_key is None:
        
        encoded_page_key = None
        
    else:
        
        encoded_page_key = page_key.hex()
        
    
    data_obj = ( encoded_page_key, [ hash.hex() for hash in hashes ] )
    
    data_str = json.dumps( data_obj )
    
    data_bytes = bytes( data_str, 'utf-8' )
    
    data_object.setData( 'application/hydrus-media', data_bytes )
    
    #
    
    drop_source.setMimeData( data_object )
    
    result = drop_source.exec_( flags, QC.Qt.CopyAction )
    
    return result
    
class FileDropTarget( QC.QObject ):
    
    def __init__( self, parent, filenames_callable = None, url_callable = None, media_callable = None ):
        
        QC.QObject.__init__( self, parent )
        
        self._parent = parent
        
        if parent:
            
            parent.setAcceptDrops( True )
            
        
        self._filenames_callable = filenames_callable
        self._url_callable = url_callable
        self._media_callable = media_callable
        
    
    def eventFilter( self, object, event ):
        
        if event.type() == QC.QEvent.Drop:
            
            if self.OnDrop( event.pos().x(), event.pos().y() ):

                event.setDropAction( self.OnData( event.mimeData(), event.proposedAction() ) )
                event.accept()
                
            
        elif event.type() == QC.QEvent.DragEnter:
            
            event.accept()
            
        
        return False
        
    
    def OnData( self, mime_data, result ):
        
        if mime_data.formats():

            if mime_data.formats().count( 'application/hydrus-media' ) and self._media_callable is not None:

                mview = mime_data.data( 'application/hydrus-media' )

                data_bytes = mview.data()

                data_str = str( data_bytes, 'utf-8' )

                (encoded_page_key, encoded_hashes) = json.loads( data_str )

                if encoded_page_key is not None:
                    
                    page_key = bytes.fromhex( encoded_page_key )
                    hashes = [ bytes.fromhex( encoded_hash ) for encoded_hash in encoded_hashes ]

                    QP.CallAfter( self._media_callable, page_key, hashes )  # callafter so we can terminate dnd event now
                    

                result = QC.Qt.MoveAction
                
            elif mime_data.hasUrls() and self._filenames_callable is not None:
                
                paths = []
                urls = []
                
                for url in mime_data.urls():
                    
                    if url.isLocalFile():
                        
                        paths.append( os.path.normpath( url.toLocalFile() ) )
                        
                    else:
                        
                        urls.append( url.url() )
                        
                    
                
                if len( paths ) > 0:
                    
                    QP.CallAfter( self._filenames_callable, paths ) # callafter to terminate dnd event now
                    
                
                if len( urls ) > 0:
                    
                    for url in urls:
                        
                        QP.CallAfter( self._url_callable, url ) # callafter to terminate dnd event now
                        
                    
                
                result = QC.Qt.IgnoreAction
                
            elif mime_data.hasText() and self._url_callable is not None:
                
                text = mime_data.text()
                
                QP.CallAfter( self._url_callable, text ) # callafter to terminate dnd event now
                
                result = QC.Qt.CopyAction
                
            else:                      
                
                result = QC.Qt.MoveAction
                
            
        
        return result
        
    
    def OnDrop( self, x, y ):
        
        screen_position = ClientGUIFunctions.ClientToScreen( self._parent, ( x, y ) )
        
        drop_tlp = QW.QApplication.topLevelAt( screen_position )
        my_tlp = self._parent.window()
        
        if drop_tlp == my_tlp:
            
            return True
            
        else:
            
            return False
            
        
    
    # setting OnDragOver to return copy gives Linux trouble with page tab drops with shift held down
