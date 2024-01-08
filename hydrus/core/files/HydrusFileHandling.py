import hashlib
import os

from hydrus.core import HydrusConstants as HC
from hydrus.core import HydrusData
from hydrus.core import HydrusExceptions
from hydrus.core import HydrusPaths
from hydrus.core import HydrusSerialisable
from hydrus.core import HydrusTemp
from hydrus.core import HydrusText
from hydrus.core.files import HydrusAnimationHandling
from hydrus.core.files import HydrusArchiveHandling
from hydrus.core.files import HydrusClipHandling
from hydrus.core.files import HydrusDocumentHandling
from hydrus.core.files import HydrusFlashHandling
from hydrus.core.files import HydrusKritaHandling
from hydrus.core.files import HydrusPDFHandling
from hydrus.core.files import HydrusProcreateHandling
from hydrus.core.files import HydrusPSDHandling
from hydrus.core.files import HydrusSVGHandling
from hydrus.core.files import HydrusUgoiraHandling
from hydrus.core.files import HydrusVideoHandling
from hydrus.core.files.images import HydrusImageHandling
from hydrus.core.networking import HydrusNetwork

try:
    
    import speedcopy
    
    speedcopy.patch_copyfile()
    
    SPEEDCOPY_OK = True
    
except Exception as e:
    
    if not isinstance( e, ImportError ):
        
        HydrusData.Print( 'Failed to initialise speedcopy:' )
        HydrusData.PrintException( e )
        
    
    SPEEDCOPY_OK = False
    


def GenerateThumbnailBytes( path, target_resolution, mime, duration, num_frames, percentage_in = 35 ):
    
    thumbnail_numpy = GenerateThumbnailNumPy( path, target_resolution, mime, duration, num_frames, percentage_in = percentage_in )

    return HydrusImageHandling.GenerateThumbnailBytesFromNumPy( thumbnail_numpy )
    

def GenerateThumbnailNumPy( path, target_resolution, mime, duration, num_frames, percentage_in = 35 ):
    
    if mime == HC.APPLICATION_CBZ:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            HydrusArchiveHandling.ExtractCoverPage( path, temp_path )
            
            cover_mime = GetMime( temp_path )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, cover_mime )
            
        except:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'zip.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    elif mime == HC.APPLICATION_CLIP:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            HydrusClipHandling.ExtractDBPNGToPath( path, temp_path )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, HC.IMAGE_PNG )
            
        except:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'clip.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    elif mime == HC.APPLICATION_KRITA:
        
        try:
            
            thumbnail_numpy = HydrusKritaHandling.GenerateThumbnailNumPyFromKraPath( path, target_resolution )
            
        except Exception as e:
            
            if not isinstance( e, HydrusExceptions.NoThumbnailFileException ):
                
                HydrusData.Print( 'Problem generating thumbnail for "{}":'.format( path ) )
                HydrusData.PrintException( e )
                
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'krita.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        
    elif mime == HC.APPLICATION_PROCREATE:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            HydrusProcreateHandling.ExtractZippedThumbnailToPath( path, temp_path )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, HC.IMAGE_PNG )
            
        except Exception as e:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'procreate.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    elif mime == HC.APPLICATION_PSD:
        
        try:
            
            thumbnail_numpy = HydrusPSDHandling.GenerateThumbnailNumPyFromPSDPath( path, target_resolution )
            
        except Exception as e:
            
            HydrusData.Print( 'Problem generating thumbnail for "{}":'.format( path ) )
            HydrusData.PrintException( e )
            HydrusData.Print( 'Attempting ffmpeg PSD thumbnail fallback' )
            
            ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath( suffix = '.png' )
            
            try:
                
                HydrusVideoHandling.RenderImageToImagePath( path, temp_path )
                
                thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, HC.IMAGE_PNG )
                
            except Exception as e: 
                
                thumb_path = os.path.join( HC.STATIC_DIR, 'psd.png' )
                
                thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
                
            finally:
                
                HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
                
            
        
    elif mime == HC.IMAGE_SVG: 
        
        try:
            
            thumbnail_numpy = HydrusSVGHandling.GenerateThumbnailNumPyFromSVGPath( path, target_resolution )
            
        except Exception as e:
            
            if not isinstance( e, HydrusExceptions.NoThumbnailFileException ):
                
                HydrusData.Print( 'Problem generating thumbnail for "{}":'.format( path ) )
                HydrusData.PrintException( e )
                
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'svg.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        
    elif mime == HC.APPLICATION_PDF:
        
        try:
            
            thumbnail_numpy = HydrusPDFHandling.GenerateThumbnailNumPyFromPDFPath( path, target_resolution )
            
        except Exception as e:
            
            if not isinstance( e, HydrusExceptions.NoThumbnailFileException ):
                
                HydrusData.Print( 'Problem generating thumbnail for "{}":'.format( path ) )
                HydrusData.PrintException( e )
                
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'pdf.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        
    elif mime == HC.APPLICATION_FLASH:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            HydrusFlashHandling.RenderPageToFile( path, temp_path, 1 )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, HC.IMAGE_PNG )
            
        except:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'flash.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    elif mime in HC.IMAGES:
        
        # TODO: it would be nice to have gif and apng generating their thumb x frames in, like with videos. maybe we should add animation thumb fetcher to hydrusanimationhandling
        
        try:
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( path, target_resolution, mime )
            
        except Exception as e:
            
            HydrusData.Print( 'Problem generating thumbnail for "{}":'.format( path ) )
            HydrusData.PrintException( e )
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'hydrus.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        
    elif mime == HC.ANIMATION_UGOIRA:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            desired_thumb_frame_index = int( ( percentage_in / 100.0 ) * ( num_frames - 1 ) )
            
            HydrusUgoiraHandling.ExtractFrame( path, desired_thumb_frame_index, temp_path )
            
            cover_mime = GetMime( temp_path )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( temp_path, target_resolution, cover_mime )
            
        except:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'zip.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    else: # animations and video
        
        renderer = None
        
        desired_thumb_frame_index = int( ( percentage_in / 100.0 ) * ( num_frames - 1 ) )
        
        try:
            
            renderer = HydrusVideoHandling.VideoRendererFFMPEG( path, mime, duration, num_frames, target_resolution, start_pos = desired_thumb_frame_index )
            
            numpy_image = renderer.read_frame()
            
        except Exception as e:
            
            HydrusData.Print( 'Problem generating thumbnail for "{}" at frame {} ({})--FFMPEG could not render it.'.format( path, desired_thumb_frame_index, HydrusData.ConvertFloatToPercentage( percentage_in / 100.0 ) ) )
            HydrusData.PrintException( e )
            
            numpy_image = None
            
        
        if numpy_image is None and desired_thumb_frame_index != 0:
            
            if renderer is not None:
                
                renderer.Stop()
                
            
            # try first frame instead
            
            try:
                
                renderer = HydrusVideoHandling.VideoRendererFFMPEG( path, mime, duration, num_frames, target_resolution )
                
                numpy_image = renderer.read_frame()
                
            except Exception as e:
                
                HydrusData.Print( 'Problem generating thumbnail for "{}" at first frame--FFMPEG could not render it.'.format( path ) )
                HydrusData.PrintException( e )
                
                numpy_image = None
                
            
        
        if numpy_image is None:
            
            thumb_path = os.path.join( HC.STATIC_DIR, 'hydrus.png' )
            
            thumbnail_numpy = HydrusImageHandling.GenerateThumbnailNumPyFromStaticImagePath( thumb_path, target_resolution, HC.IMAGE_PNG )
            
        else:
            
            thumbnail_numpy =  HydrusImageHandling.ResizeNumPyImage( numpy_image, target_resolution ) # just in case ffmpeg doesn't deliver right
            
        
        if renderer is not None:
            
            renderer.Stop()
            
        
    
    return thumbnail_numpy
    
def GetExtraHashesFromPath( path ):
    
    h_md5 = hashlib.md5()
    h_sha1 = hashlib.sha1()
    h_sha512 = hashlib.sha512()
    
    with open( path, 'rb' ) as f:
        
        for block in HydrusPaths.ReadFileLikeAsBlocks( f ):
            
            h_md5.update( block )
            h_sha1.update( block )
            h_sha512.update( block )
            
        
    
    md5 = h_md5.digest()
    sha1 = h_sha1.digest()
    sha512 = h_sha512.digest()
    
    return ( md5, sha1, sha512 )
    

def GetFileInfo( path, mime = None, ok_to_look_for_hydrus_updates = False ):
    
    size = os.path.getsize( path )
    
    if size == 0:
        
        raise HydrusExceptions.ZeroSizeFileException( 'File is of zero length!' )
        
    
    if mime is None:
        
        mime = GetMime( path, ok_to_look_for_hydrus_updates = ok_to_look_for_hydrus_updates )
        
    
    if mime not in HC.ALLOWED_MIMES:
        
        if mime == HC.TEXT_HTML:
            
            raise HydrusExceptions.UnsupportedFileException( 'Looks like HTML -- maybe the client needs to be taught how to parse this?' )
            
        elif mime == HC.APPLICATION_UNKNOWN:
            
            raise HydrusExceptions.UnsupportedFileException( 'Unknown filetype!' )
            
        else:
            
            raise HydrusExceptions.UnsupportedFileException( 'Filetype is not permitted!' )
            
        
    
    if mime in HC.PIL_HEIF_MIMES and not HydrusImageHandling.HEIF_OK:
        
        raise HydrusExceptions.UnsupportedFileException( 'Sorry, you need the pillow-heif library to support this filetype ({})! Please rebuild your venv.'.format( HC.mime_string_lookup[ mime ] ) )
        
    
    width = None
    height = None
    duration = None
    num_frames = None
    num_words = None
    
    if mime in HC.MIMES_THAT_DEFINITELY_HAVE_AUDIO:
        
        has_audio = True
        
    else:
        
        has_audio = False
        
    
    # keep this in the specific-first, general-last test order
    if mime == HC.APPLICATION_CBZ:
        
        ( os_file_handle, temp_path ) = HydrusTemp.GetTempPath()
        
        try:
            
            HydrusArchiveHandling.ExtractCoverPage( path, temp_path )
            
            cover_mime = GetMime( temp_path )
            
            ( width, height ) = HydrusImageHandling.GetImageResolution( temp_path, cover_mime )
            
        except:
            
            ( width, height ) = ( 100, 100 )
            
        finally:
            
            HydrusTemp.CleanUpTempPath( os_file_handle, temp_path )
            
        
    elif mime == HC.APPLICATION_CLIP:
        
        ( ( width, height ), duration, num_frames ) = HydrusClipHandling.GetClipProperties( path )
        
    elif mime == HC.APPLICATION_KRITA:
        
        try:
            
            ( width, height ) = HydrusKritaHandling.GetKraProperties( path )
            
        except HydrusExceptions.NoResolutionFileException:
            
            pass
            
        
    elif mime == HC.APPLICATION_PROCREATE:
        
        try:
            
            ( width, height ) = HydrusProcreateHandling.GetProcreateResolution( path )
            
        except:
            
            pass
            
        
    elif mime == HC.IMAGE_SVG:
        
        try:
            
            ( width, height ) = HydrusSVGHandling.GetSVGResolution( path )
            
        except HydrusExceptions.NoResolutionFileException:
            
            pass
            
        
    elif mime == HC.APPLICATION_PDF:
        
        try:
            
            ( num_words, ( width, height ) ) = HydrusPDFHandling.GetPDFInfo( path )
            
        except HydrusExceptions.LimitedSupportFileException:
            
            pass
            
        
    elif mime == HC.APPLICATION_FLASH:
        
        ( ( width, height ), duration, num_frames ) = HydrusFlashHandling.GetFlashProperties( path )
        
    elif mime == HC.APPLICATION_PDF:
        
        num_words = HydrusDocumentHandling.GetPDFNumWords( path ) # this now give None until a better solution can be found
        
    elif mime == HC.APPLICATION_PSD:
        
        try:
            
            ( width, height ) = HydrusPSDHandling.GetPSDResolution( path )
            
        except Exception as e:
            
            HydrusData.Print( 'Problem calculating resolution for "{}":'.format( path ) )
            HydrusData.PrintException( e )
            HydrusData.Print( 'Attempting PSD resolution fallback' )

            ( width, height ) = HydrusPSDHandling.GetPSDResolutionFallback( path )
            
        
    elif mime in HC.VIDEO or mime in HC.HEIF_TYPE_SEQUENCES:
        
        ( ( width, height ), duration, num_frames, has_audio ) = HydrusVideoHandling.GetFFMPEGVideoProperties( path )
        
    elif mime in HC.VIEWABLE_ANIMATIONS:
        
        ( ( width, height ), duration, num_frames ) = HydrusAnimationHandling.GetAnimationProperties( path, mime )
        
    elif mime == HC.ANIMATION_UGOIRA:
        
        ( ( width, height ), num_frames ) = HydrusUgoiraHandling.GetUgoiraProperties( path )
        
    elif mime in HC.IMAGES:
        
        ( width, height ) = HydrusImageHandling.GetImageResolution( path, mime )
        
    elif mime in HC.AUDIO:
        
        ffmpeg_lines = HydrusVideoHandling.GetFFMPEGInfoLines( path )
        
        ( file_duration_in_s, stream_duration_in_s ) = HydrusVideoHandling.ParseFFMPEGDuration( ffmpeg_lines )
        
        duration = int( file_duration_in_s * 1000 )
        
    
    if width is not None and width < 0:
        
        width *= -1
        
    
    if height is not None and height < 0:
        
        width *= -1
        
    
    if duration is not None and duration < 0:
        
        duration *= -1
        
    
    if num_frames is not None and num_frames < 0:
        
        num_frames *= -1
        
    
    if num_words is not None and num_words < 0:
        
        num_words *= -1
        
    
    return ( size, mime, width, height, duration, num_frames, has_audio, num_words )
    

def GetFileModifiedTimestamp( path ) -> int:
    
    return int( os.path.getmtime( path ) )
    

def GetHashFromPath( path ):
    
    h = hashlib.sha256()
    
    with open( path, 'rb' ) as f:
        
        for block in HydrusPaths.ReadFileLikeAsBlocks( f ):
            
            h.update( block )
            
        
    
    return h.digest()
    

# TODO: replace this with a FileTypeChecker class or something that tucks all this messy data away more neatly
# do this the next time you visit this place
headers_and_mime = [
    ( ( ( [0], [b'\xff\xd8'] ), ), HC.IMAGE_JPEG ),
    ( ( ( [0], [b'\x89PNG'] ), ), HC.UNDETERMINED_PNG ),
    ( ( ( [0], [b'GIF87a', b'GIF89a'] ), ), HC.UNDETERMINED_GIF ),
    ( ( ( [8], [b'WEBP'] ), ), HC.IMAGE_WEBP ),
    ( ( ( [0], [b'II*\x00', b'MM\x00*'] ), ), HC.IMAGE_TIFF ),
    ( ( ( [0], [b'BM'] ), ), HC.IMAGE_BMP ),
    ( ( ( [0], [b'\x00\x00\x01\x00', b'\x00\x00\x02\x00'] ), ), HC.IMAGE_ICON ),
    ( ( ( [0], [b'qoif'] ), ), HC.IMAGE_QOI ),
    ( ( ( [0], [b'CWS', b'FWS', b'ZWS'] ), ), HC.APPLICATION_FLASH ),
    ( ( ( [0], [b'FLV'] ), ), HC.VIDEO_FLV ),
    ( ( ( [0], [b'%PDF'] ), ), HC.APPLICATION_PDF ),
    ( ( ( [0], [b'8BPS\x00\x01', b'8BPS\x00\x02'] ), ), HC.APPLICATION_PSD ),
    ( ( ( [0], [b'CSFCHUNK'] ), ), HC.APPLICATION_CLIP ),
    ( ( ( [0], [b'SAI-CANVAS'] ), ), HC.APPLICATION_SAI2 ),
    ( ( ( [0], [b'gimp xcf '] ), ), HC.APPLICATION_XCF ),
    ( ( ( [38, 42, 58, 63],[ b'application/x-krita'] ), ), HC.APPLICATION_KRITA ), # important this comes before zip files because this is also a zip file
    ( ( ( [38, 43],[ b'application/epub+zip'] ), ), HC.APPLICATION_EPUB ),
    ( ( ( [4], [b'FORM'] ), ( [12], [b'DJVU', b'DJVM', b'PM44', b'BM44', b'SDJV'] ), ), HC.APPLICATION_DJVU ),
    ( ( ( [0], [b'{\\rtf'] ), ), HC.APPLICATION_RTF ),
    ( ( ( [0], [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'] ), ), HC.APPLICATION_ZIP ),
    ( ( ( [0], [b'7z\xBC\xAF\x27\x1C'] ), ), HC.APPLICATION_7Z ),
    ( ( ( [0], [b'\x52\x61\x72\x21\x1A\x07\x00', b'\x52\x61\x72\x21\x1A\x07\x01\x00'] ), ), HC.APPLICATION_RAR ),
    ( ( ( [0], [b'\x1f\x8b'] ), ), HC.APPLICATION_GZIP ),
    ( ( ( [0], [b'hydrus encrypted zip'] ), ), HC.APPLICATION_HYDRUS_ENCRYPTED_ZIP ),
    ( ( ( [4], [b'ftypavif'] ), ), HC.IMAGE_AVIF ),
    ( ( ( [4], [b'ftypavis'] ), ), HC.IMAGE_AVIF_SEQUENCE ),
    ( ( ( [4], [b'ftypmif1'] ), ( [16, 20, 24], [b'avif'] ), ), HC.IMAGE_AVIF ),
    ( ( ( [4], [b'ftypheic', b'ftypheix', b'ftypheim', b'ftypheis'] ), ), HC.IMAGE_HEIC ),
    ( ( ( [4], [b'ftyphevc', b'ftyphevx', b'ftyphevm', b'ftyphevs'] ), ), HC.IMAGE_HEIC_SEQUENCE ),
    ( ( ( [4], [b'ftypmif1'] ), ), HC.IMAGE_HEIF ),
    ( ( ( [4], [b'ftypmsf1'] ), ), HC.IMAGE_HEIF_SEQUENCE ),
    ( ( ( [4], [b'ftypmp4', b'ftypisom', b'ftypM4V', b'ftypMSNV', b'ftypavc1', b'ftypavc1', b'ftypFACE', b'ftypdash'] ), ), HC.UNDETERMINED_MP4 ),
    ( ( ( [4], [b'ftypqt'] ), ), HC.VIDEO_MOV ),
    ( ( ( [0], [b'fLaC'] ), ), HC.AUDIO_FLAC ),
    ( ( ( [0], [b'RIFF'] ), ( [8], [ b'WAVE' ] ) ), HC.AUDIO_WAVE ),
    ( ( ( [0], [b'wvpk'] ), ), HC.AUDIO_WAVPACK ),
    ( ( ( [8], [b'AVI '] ), ), HC.VIDEO_AVI ),
    ( ( ( [0], [b'\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C'] ), ), HC.UNDETERMINED_WM ),
    ( ( ( [0], [b'\x4D\x5A\x90\x00\x03'], ), ), HC.APPLICATION_WINDOWS_EXE )
]

def passes_offsets_and_headers_pair( offsets, headers, first_bytes_of_file ) -> bool:
    # TODO: rewrite this garbage
    
    for offset in offsets:
        
        for header in headers:
            
            if first_bytes_of_file[ offset : offset + len( header ) ] == header:
                
                return True
                
            
        
    
    return False
    

def passes_offsets_and_headers( offsets_and_headers, first_bytes_of_file ) -> bool:
    
    # ok we need to match every pair here
    for ( offsets, headers ) in offsets_and_headers:
        
        if not passes_offsets_and_headers_pair( offsets, headers, first_bytes_of_file ):
            
            return False
            
        
    
    return True
    

def GetMime( path, ok_to_look_for_hydrus_updates = False ):
    
    size = os.path.getsize( path )
    
    if size == 0:
        
        raise HydrusExceptions.ZeroSizeFileException( 'File is of zero length!' )
        
    
    if ok_to_look_for_hydrus_updates and size < 64 * 1024 * 1024:
        
        with open( path, 'rb' ) as f:
            
            update_network_bytes = f.read()
            
        
        try:
            
            update = HydrusSerialisable.CreateFromNetworkBytes( update_network_bytes )
            
            if isinstance( update, HydrusNetwork.ContentUpdate ):
                
                return HC.APPLICATION_HYDRUS_UPDATE_CONTENT
                
            elif isinstance( update, HydrusNetwork.DefinitionsUpdate ):
                
                return HC.APPLICATION_HYDRUS_UPDATE_DEFINITIONS
                
            
        except:
            
            pass
            
        
    
    with open( path, 'rb' ) as f:
        
        first_bytes_of_file = f.read( 256 )
        
    
    for ( offsets_and_headers, mime ) in headers_and_mime:
        
        if passes_offsets_and_headers( offsets_and_headers, first_bytes_of_file ):
            
            if mime == HC.APPLICATION_ZIP:
                
                try:
                    
                    if HydrusArchiveHandling.IsEncryptedZip( path ):
                        
                        return HC.APPLICATION_ZIP
                        
                    
                except HydrusExceptions.DamagedOrUnusualFileException:
                    
                    return HC.APPLICATION_ZIP
                    
                
                opendoc_mime = HydrusArchiveHandling.MimeFromOpenDocument( path )

                if opendoc_mime is not None:
                    
                    return opendoc_mime
                    
                
                if HydrusProcreateHandling.ZipLooksLikeProcreate( path ):
                    
                    return HC.APPLICATION_PROCREATE
                    
                
                if HydrusUgoiraHandling.ZipLooksLikeUgoira( path ):
                    
                    return HC.ANIMATION_UGOIRA
                    
                
                if HydrusArchiveHandling.ZipLooksLikeCBZ( path ):
                    
                    return HC.APPLICATION_CBZ
                    
                
                return HC.APPLICATION_ZIP
                
            if mime in ( HC.UNDETERMINED_WM, HC.UNDETERMINED_MP4 ):
                
                return HydrusVideoHandling.GetMime( path )
                
            elif mime == HC.UNDETERMINED_PNG:
                
                if HydrusAnimationHandling.IsPNGAnimated( first_bytes_of_file ):
                    
                    return HC.ANIMATION_APNG
                    
                else:
                    
                    return HC.IMAGE_PNG
                    
                
            elif mime == HC.UNDETERMINED_GIF:
                
                if HydrusAnimationHandling.PILAnimationHasDuration( path ):
                    
                    return HC.ANIMATION_GIF
                    
                else:
                    
                    return HC.IMAGE_GIF
                    
                
            else:
                
                return mime
                
            
        
    
    # If the file starts with '{' it is probably JSON
    # but we can't know for sure so we send it over to be checked
    if first_bytes_of_file.startswith( b'{' ) or first_bytes_of_file.startswith( b'[' ):
        
        with open( path, 'rb' ) as f:
            
            potential_json_document_bytes = f.read()
            
            if HydrusText.LooksLikeJSON( potential_json_document_bytes ):
                
                return HC.APPLICATION_JSON
                
            
        
    
    if HydrusText.LooksLikeHTML( first_bytes_of_file ):
        
        return HC.TEXT_HTML
        
    
    if HydrusText.LooksLikeSVG( first_bytes_of_file ): 
        
        return HC.IMAGE_SVG
        
    
    # it is important this goes at the end, because ffmpeg has a billion false positives! and it takes CPU to true negative
    # for instance, it once thought some hydrus update files were mpegs
    # it also thinks txt files can be mpegs
    likely_to_false_positive = True in ( path.endswith( ext ) for ext in ( '.txt', '.log', '.json' ) )
    
    if not likely_to_false_positive:
        
        try:
            
            mime = HydrusVideoHandling.GetMime( path )
            
            if mime != HC.APPLICATION_UNKNOWN:
                
                return mime
                
            
        except HydrusExceptions.UnsupportedFileException:
            
            pass
            
        except Exception as e:
            
            HydrusData.Print( 'FFMPEG had trouble with: ' + path )
            HydrusData.PrintException( e, do_wait = False )
            
        
    
    return HC.APPLICATION_UNKNOWN
    

headers_and_mime_thumbnails = [ ( offsets_and_headers, mime ) for ( offsets_and_headers, mime ) in headers_and_mime if mime in ( HC.IMAGE_JPEG, HC.IMAGE_PNG ) ]

def GetThumbnailMime( path ):
    
    with open( path, 'rb' ) as f:
        
        bit_to_check = f.read( 256 )
        
    
    for ( offsets_and_headers, mime ) in headers_and_mime_thumbnails:
        
        if passes_offsets_and_headers( offsets_and_headers, bit_to_check ):
            
            return mime
            
        
    
    return GetMime( path )
    