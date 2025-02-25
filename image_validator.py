import os
from PIL import Image
import subprocess

class ImageValidator:
    def __init__(self):
        self.valid_extensions = ('.jpg', '.jpeg', '.tif', '.tiff')
        self.min_width = 1200
        self.min_height = 1200

    def validate_product_image(self, image_path):
        """Validera produktbild"""
        try:
            print(f"Validating image: {image_path}")
            
            # Kontrollera filtyp
            if not image_path.lower().endswith(self.valid_extensions):
                return False, f"Ogiltig filtyp. Måste vara: {self.valid_extensions}"
            
            # Öppna och kontrollera bilden
            with Image.open(image_path) as img:
                width, height = img.size
                print(f"Image dimensions: {width}x{height}")
                
                if width < self.min_width or height < self.min_height:
                    return False, f"Bilden är för liten. Minimum är {self.min_width}x{self.min_height}"
                
            return True, "Bilden är giltig"
            
        except Exception as e:
            print(f"Error validating image: {str(e)}")
            return False, str(e)

    def convert_to_planogram(self, input_path, output_path):
        """Konvertera till planogram med ImageMagick"""
        try:
            print(f"\nCreating planogram from validated JPG...")
            print(f"Input image: {input_path}")
            
            # Använd subprocess istället för os.system för bättre felhantering
            command = [
                'magick',
                input_path,
                '-alpha', 'transparent',
                '-clip',
                '-alpha', 'opaque',
                '-resize', '1200',
                output_path
            ]
            
            print(f"Running command: {' '.join(command)}")
            
            result = subprocess.run(command, 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print(f"Planogram saved to: {output_path}")
                return True, "Planogram created successfully with transparency"
            else:
                error_msg = f"ImageMagick error: {result.stderr}"
                print(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error creating planogram: {str(e)}"
            print(error_msg)
            return False, error_msg

    def _extract_paths_as_mask(self, img):
        """Helper method to extract paths as a mask"""
        try:
            mask = img.clone()
            mask.format = 'PNG'
            mask.alpha_channel = 'extract'
            
            # Try different methods to extract paths
            for method in ['8bim:clipping-path', 'path:clipping-path']:
                try:
                    mask.clipping_path = method
                    return mask
                except Exception:
                    continue
            
            return None
        except Exception as e:
            print(f"Error extracting paths: {e}")
            return None

    def _create_mask_from_path(self, path_data, size):
        from PIL import Image, ImageDraw
        import numpy as np
        
        # Skapa en tom mask med vit bakgrund
        mask = Image.new('L', size, 0)  # L = 8-bit pixels, svart och vitt
        draw = ImageDraw.Draw(mask)
        
        # Tolka bandata
        # Path data är en lista av tupler: (selector, (x,y)...)
        points = []
        for selector, *coords in path_data:
            if selector == 0:  # Moveto
                if points:  # Rita föregående segment om det finns några punkter
                    draw.polygon(points, fill=255)
                points = []
                points.extend([coord[0] for coord in coords])
            elif selector == 1:  # Lineto
                points.extend([coord[0] for coord in coords])
            elif selector == 2:  # Curveto (Bezier)
                # För varje Bezier-kurva får vi 3 punkter: två kontrollpunkter och en slutpunkt
                for i in range(0, len(coords), 3):
                    if i + 2 < len(coords):
                        # Approximera Bezier-kurvan med linjesegment
                        start = points[-2:] if points else coords[i][0]
                        control1 = coords[i][0]
                        control2 = coords[i+1][0]
                        end = coords[i+2][0]
                        
                        # Skapa punkter längs Bezier-kurvan
                        for t in np.linspace(0, 1, 20):
                            # Bezier-kurva formel
                            x = (1-t)**3 * start[0] + 3*(1-t)**2 * t * control1[0] + \
                                3*(1-t) * t**2 * control2[0] + t**3 * end[0]
                            y = (1-t)**3 * start[1] + 3*(1-t)**2 * t * control1[1] + \
                                3*(1-t) * t**2 * control2[1] + t**3 * end[1]
                            points.extend([x, y])
            elif selector == 3:  # Closepath
                if points:
                    draw.polygon(points, fill=255)
                points = []
        
        # Rita eventuella kvarvarande punkter
        if points:
            draw.polygon(points, fill=255)
        
        return mask