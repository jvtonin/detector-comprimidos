import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageOps
import numpy as np
from scipy import ndimage


class AplicacaoComprimidos:
    def __init__(self, root):
        self.root = root
        self.root.title("Detector de Comprimidos")
        self.root.geometry("900x700")

        frame_imagens = tk.Frame(root)
        frame_imagens.pack(pady=10)

        self.canvas_original = tk.Label(frame_imagens)
        self.canvas_original.grid(row=0, column=0, padx=20)

        self.canvas_processada = tk.Label(frame_imagens)
        self.canvas_processada.grid(row=0, column=1, padx=20)

        self.botao_carregar = tk.Button(root, text="Selecionar Imagem", font=("Arial", 14), command=self.carregar_imagem)
        self.botao_carregar.pack(pady=10)

        self.resultado = tk.Label(root, text="", font=("Arial", 14), justify="center")
        self.resultado.pack(pady=10)

    def carregar_imagem(self):
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if not caminho:
            return

        try:
            self.imagem_original = Image.open(caminho).convert("RGB")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir imagem:\n{e}")
            return

        imagem_thumb = self.imagem_original.copy()
        imagem_thumb.thumbnail((400, 400))
        imagem_tk = ImageTk.PhotoImage(imagem_thumb)
        self.canvas_original.configure(image=imagem_tk)
        self.canvas_original.image = imagem_tk

        imagem_processada, total, quebrados, redondos, capsulas = self.processar(self.imagem_original.copy())

        imagem_thumb_proc = imagem_processada.copy()
        imagem_thumb_proc.thumbnail((400, 400))
        imagem_tk_proc = ImageTk.PhotoImage(imagem_thumb_proc)
        self.canvas_processada.configure(image=imagem_tk_proc)
        self.canvas_processada.image = imagem_tk_proc

        texto = (
            f"Total de comprimidos: {total}\n"
            f"Comprimidos quebrados: {quebrados}\n"
            f"Redondos: {redondos}\n"
            f"Cápsulas: {capsulas}"
        )
        self.resultado.config(text=texto)

    def processar(self, imagem_pil):
        imagem_cinza = imagem_pil.convert("L").filter(ImageFilter.GaussianBlur(radius=2))

        np_gray = np.array(imagem_cinza)
        limiar = np_gray.mean()
        binaria = (np_gray < limiar).astype(np.uint8)

        binaria = 1 - binaria

        binaria = ndimage.binary_opening(binaria, structure=np.ones((3, 3))).astype(np.uint8)

        etiquetas, num = ndimage.label(binaria)
        objetos = ndimage.find_objects(etiquetas)

        imagem_rgb = imagem_pil.convert("RGB")
        pixels = imagem_rgb.load()

        total = quebrados = redondos = capsulas = 0

        for i, obj in enumerate(objetos):
            slice_x, slice_y = obj
            largura = slice_y.stop - slice_y.start
            altura = slice_x.stop - slice_x.start
            area = largura * altura

            if area < 500 or area > imagem_pil.width * imagem_pil.height * 0.5:
                continue

            total += 1

            razao = max(largura, altura) / min(largura, altura)


            regiao = (etiquetas[slice_x, slice_y] == (i + 1)).astype(np.uint8)
            solidez = np.sum(regiao) / area
            if solidez < 0.65:
                capsulas += 1
                cor = (255,255,0)
            else: 
                if razao < 1.3:
                    redondos += 1
                    cor = (0, 255, 0)
                else:
                    quebrados += 1
                    cor = (255, 0, 0)



            for x in range(slice_y.start, slice_y.stop):
                pixels[x, slice_x.start] = cor
                pixels[x, slice_x.stop - 1] = cor
            for y in range(slice_x.start, slice_x.stop):
                pixels[slice_y.start, y] = cor
                pixels[slice_y.stop - 1, y] = cor

        return imagem_rgb, total, quebrados, redondos, capsulas


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoComprimidos(root)
    root.mainloop()
