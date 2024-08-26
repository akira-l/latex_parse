



# EasyInv: Toward Fast and Better DDIM Inversion


This paper introduces EasyInv, an easy yet novel approach that significantly advances the field of DDIM Inversion by addressing the inherent inefficiencies and performance limitations of traditional iterative optimization methods. At the core of our EasyInv is a refined strategy for approximating inversion noise, which is pivotal for enhancing the accuracy and reliability of the inversion process. By prioritizing the initial latent state, which encapsulates rich information about the original images, EasyInv steers clear of the iterative refinement of noise items. Instead, we introduce a methodical aggregation of the latent state from the preceding time step with the current state, effectively increasing the influence of the initial latent state and mitigating the impact of noise. We illustrate that EasyInv is capable of delivering results that are either on par with or exceed those of the conventional DDIM Inversion approach, especially under conditions where the model's precision is limited or computational resources are scarce. Concurrently, our EasyInv offers an approximate threefold enhancement regarding inference efficiency over off-the-shelf iterative optimization techniques.

Diffusion models have become a major focus of research in recent years, mostly renowned for their ability to generate high-quality images that closely match given prompts. Among the many diffusion models introduced in the community, Stable Diffusion (SD) BIBREF0 stands out as one of the most widely utilized in scientific research, largely due to its open-source nature. Another contemporary diffusion model gaining popularity is DALL-E 3 BIBREF1 , which offers users access to its API and the ability to interact with it through platforms like ChatGPT BIBREF2 . These models have significantly transformed the visual arts industry and have attracted substantial attention from the research community.

While renowned generative diffusion models have made significant strides, a prevalent limitation is their reliance on textual prompts for input. This approach becomes restrictive when users seek to iteratively refine an image, as the sole reliance on prompts hinders flexibility. Although solutions such as ObjectAdd BIBREF3 and P2P BIBREF4 have been proposed to address image editing challenges, they are still confined to the realm of prompted image manipulation. Given that diffusion models generate images from noise inputs, a potential breakthrough lies in identifying the corresponding noise for any given image. This would enable the diffusion model to initiate the generation process from a known starting point, thereby allowing for precise control over the final output. The recent innovation of DDIM Inversion BIBREF5 aims to overcome this challenge by reversing the denoising process to introduce noise. This technique effectively retrieves the initial noise configuration after a series of reference steps, thereby preserving the integrity of the original image while affording the user the ability to manipulate the output by adjusting the denoising parameters. With DDIM inversion, the generative process becomes more adaptable, facilitating the creation and subsequent editing of images with greater precision and control. For example, the MasaCtrl method BIBREF6 first transforms a real image into a noise representation and then identifies the arrangement of objects during the denoising phase. Portrait Diffusion BIBREF7 simultaneously inverts both the source and target images. Subsequently, it merges their respective INLINEFORM0 , INLINEFORM1 and INLINEFORM2 values for mixups.

Considering the reliance on inversion techniques to preserve the integrity of the input image, the quality of the inversion process is paramount, as it profoundly influences subsequent tasks. As depicted in Figure FIGREF1 (a), the performance of DDIM Inversion has been found to be less than satisfactory due to the discrepancy between the noise estimated during the inversion process and the noise expected in the sampling process. Consequently, numerous studies have been conducted to enhance its efficacy. In Null-Text inversion BIBREF10 , researchers observed that using a null prompt as input, the diffusion model could generate optimal results during inversion, suggesting that improvements to inversion might be better achieved in the reconstruction branch. Ju et al .'s work BIBREF11 exemplifies this approach by calculating the distance between latents at the current step and the previous step. PTI BIBREF12 opts to update the conditional vector in each step to guide the reconstruction branch for improving consistency. ReNoise BIBREF9 focuses on refining the inversion process itself. This method iteratively adds and then denoises noise at each time step, using the denoised noise as input for the subsequent iteration. However, as shown in Figure FIGREF1 (b), it can result in a black image output when dealing with certain special inputs, which will be discussed in detail in Sec. SECREF4 . Pan et al. BIBREF8 , while maintaining the iterative updating process, also amalgamated noise from previous steps with the current step's noise. However, this method's performance is limited in less effective models as displayed in Figure FIGREF1 (c). For instance, it performs well in SD-XL BIBREF13 but fails to yield proper results in SD-V1-4 BIBREF0 . We attribute this to their method's sole focus on optimizing noise; when the noise is highly inaccurate, such simple optimization strategies encounter difficulties. Additionally, the iterative updating of noise is time-consuming, as Pan et al. 's method requires multiple model inferences per time step.

In this paper, we conduct an in-depth analysis and recognize that the foundation of any inversion process is the initial latent state derived from a real image. Errors introduced at each step of the inversion process can accumulate, leading to a suboptimal reconstruction. Current methodologies, which focus on optimizing the transition between successive steps, may not be adequate to address this issue holistically. To tackle this, we propose a novel approach that considers the inversion process as a whole, underscoring the significance of the initial latent state throughout the process. Our approach, named EasyInv, incorporates a straightforward mechanism to periodically reinforce the influence of the initial latent state during the inversion. This is realized by blending the current latent state with the previous one at strategically selected intervals, thereby increasing the weight of the initial latent state and diminishing the noise's impact. As a result, EasyInv ensures a reconstructed version that remains closer to the original image, as illustrated in Figure FIGREF1 (d). Furthermore, by building upon the traditional DDIM Inversion framework BIBREF5 , EasyInv does not depend on iterative optimization between adjacent steps, thus enhancing computational efficiency. In Figure FIGREF2 , we present a visualization of the latent states at the midpoint of the total denoising steps for various inversion methods. It is evident that the outcomes of our EasyInv are more closely aligned with the original image compared to all other methods, demonstrating that EasyInv achieves faster convergence.

 Diffusion Model . In recent years, there has been significant progress in the field of generative models, with diffusion models emerging as a particularly popular approach. The seminal denoising diffusion probabilistic models (DDPM) BIBREF14 introduced a practical framework for image generation based on the diffusion process. This method stands out from its predecessors, such as generative adversarial networks (GANs), due to its iterative nature. During the data preparation phase, Gaussian noise is incrementally added to a real image until it transitions into a state that is indistinguishable from raw Gaussian noise. Subsequently, a model can be trained to predict the noise added at each step, enabling users to input any Gaussian noise and obtain a high-quality image as a result. Ho et al . BIBREF14 provided a robust theoretical foundation for their model, which has facilitated further advancements. Generative process in DDPM is both time-consuming and inherently stochastic due to the random noise introduced at each step. To address these limitations, the denoising diffusion implicit models (DDIM) were developed BIBREF15 . By reformulating DDPM, DDIM has successfully reduced the amount of random noise added at each step. This reformulation results in a more deterministic denoising process. Furthermore, the absence of random noise allows for the aggregation of several denoising steps, thereby significantly reducing the overall computation time required to generate an image.

 Image Inversion . Converting a real image into noise is a pivotal first step in the realm of real image editing using diffusion models. The precision of this process has a profound impact in the final edit, with the critical element being the accurate identification of the noise added at each step. Couairon et al . BIBREF5 ingeniously swapped the roles of independent and implicit variables within the denoising function of the DDIM model, enabling it to predict the noise that should be introduced to the current latents. However, it is essential to recognize that the denoising step in a diffusion model is inherently an approximation, and when this approximation is utilized inversely, discrepancies between the model's output and the actual noise value are likely to be exacerbated. To address this issue, ReNoise BIBREF9 iterates through each noising step multiple times. For each inversion step, they employ an iterative approach to add and subsequently reduce noise, with the noise reduced in the final iteration being carried forward to the subsequent iteration. Pan et al. BIBREF8 offered a theoretical underpinning to the ReNoise method. Iterative optimization from ReNoise is classified under the umbrella of fixed-point iteration methods. Building upon Anderson's seminal work BIBREF16 , Pan et al . have advanced the field by proposing their novel method for optimizing noise during the inversion process.

Let INLINEFORM0 denote a noise tensor with INLINEFORM1 . The DDIM BIBREF5 leverages a pre-trained neural network INLINEFORM2 to perform INLINEFORM3 denoising diffusion steps. Each step aims to estimate the underlying noise and subsequently restore a less noisy version of the tensor, INLINEFORM4 , from its noisy counterpart INLINEFORM5 as: 

 DISPLAYFORM0 

 where INLINEFORM0 , and INLINEFORM1 constitutes a prescribed variances set that guides the diffusion process. Furthermore, INLINEFORM2 serves as an intermediate representation that encapsulates the textual condition INLINEFORM3 . For the convenience of following sections, we denote:

 DISPLAYFORM0 

Re-evaluating Eq. ( EQREF5 ), we derive DDIM Inversion process BIBREF5 as presented in Eq.( EQREF7 ). In this reformulation, we relocate an approximate INLINEFORM0 to the left-hand side, resulting in the following expression: 

 DISPLAYFORM0 

 

 Review . Given an image INLINEFORM0 , after encoding it into the latent INLINEFORM1 , we initiate INLINEFORM2 inversion steps using Eq. ( EQREF7 ) to obtain the noise INLINEFORM3 . Starting with INLINEFORM4 , we proceed with a denoising process in Eq. ( EQREF5 ) to infer an approximate reconstruction INLINEFORM5 that resembles the original latent INLINEFORM6 . The primary source of error in this reconstruction arises from the difference between the noise predicted during the inversion process INLINEFORM7 and the noise expected in the sampling process, INLINEFORM8 , denoted as INLINEFORM9 , at each iterative step. This discrepancy originates from an imprecise approximation of the time step from INLINEFORM10 to INLINEFORM11 . Therefore, reducing the discrepancy between the predicted noises at each step is crucial for achieving an accurate reconstruction, which is essential for the success of subsequent image editing tasks. For simplicity in the following expressions, we define:

 DISPLAYFORM0 

The vanilla DDIM Inversion method, as discussed, involves an approximation that is not entirely precise for INLINEFORM0 . To address this, researchers have sought to refine a more accurate approximation of INLINEFORM1 , thereby ensuring that the desired conditions are optimally met. This refinement process aims to enhance the precision of the method, leading to more reliable results in the context of the application:

 DISPLAYFORM0 

For clarity, let's first restate Eq. ( EQREF7 ) as follows:

 DISPLAYFORM0 

which represents the introduction of adding noise to the latent state INLINEFORM0 . Under the assumption of Eq. ( EQREF10 ), it should be the case that:

 DISPLAYFORM0 

Subsequently, by employing the noise estimation function from Eq. ( EQREF6 ), we obtain:

 DISPLAYFORM0 

Given that INLINEFORM0 and considering Eq. ( EQREF10 ), we can deduce that:

 DISPLAYFORM0 

This formulation presents a fixed-point problem, which pertains to a value that remains unchanged under a specific transformation BIBREF17 . In the context of functions, a fixed point is an element that is invariant under the application of the function. In this paper, we seek a INLINEFORM0 that, when transformed by INLINEFORM1 and followed by INLINEFORM2 , can map back to itself, signifying an optimal solution as per Eq. ( EQREF10 ).

Fixed-point iteration is a computational technique designed to identify the fixed points of a function. It functions through an iterative process, as delineated below:

 DISPLAYFORM0 

where INLINEFORM0 denotes the iteration count. This iterative process can be enhanced through acceleration techniques such as Anderson acceleration BIBREF16 . However, calculating a complex INLINEFORM1 can be quite onerous. An empirical acceleration method proposed BIBREF8 introduces a refinement for INLINEFORM2 by setting: INLINEFORM3 and INLINEFORM4 . They finally reach:

 DISPLAYFORM0 

where the term INLINEFORM0 represents the refinement technique for INLINEFORM1 as suggested by Pan et al. . If we were to apply the function INLINEFORM2 to both sides of Eq. ( EQREF16 ), it would align perfectly with the form of Eq. ( EQREF15 ). Their experiments have demonstrated that this approach is more effective than both Anderson's method BIBREF16 and other techniques in inversion tasks.

Despite the progress made, this paper acknowledges inherent limitations in the practical implementation of the inversion technique: (1) Inversion Efficiency: While the method outlined in Eq. ( EQREF16 ) has shown improvements over traditional fixed-point iteration, it still relies on iterative optimization. The need for multiple forward passes through the diffusion model is computationally demanding and can result in inefficiencies in downstream applications. (2) Inversion Performance: The theoretical improvements presented assume that INLINEFORM0 . However, iterative optimization does not guarantee the exact fulfillment of Equation ( EQREF12 ) for every time step INLINEFORM1 . Therefore, while the method may theoretically offer superior performance, cumulative errors can sometimes lead to practical outcomes that are less satisfactory than those achieved with the standard DDIM Inversion method, as shown in Figure FIGREF1 .

To facilitate our subsequent analysis, we introduce the notation INLINEFORM0 to represent INLINEFORM1 and INLINEFORM2 to denote INLINEFORM3 . With these notations, we can reframe Eq. ( EQREF7 ) as follow:

 DISPLAYFORM0 

Similarly, we can express the form of INLINEFORM0 as:

 DISPLAYFORM0 

By combining these two formulas, we derive:

 DISPLAYFORM0 

This can be further generalized to:

 DISPLAYFORM0 

From Eq. ( EQREF21 ), it is evident that INLINEFORM0 is a weighted sum of INLINEFORM1 and a series of noise terms INLINEFORM2 . The denoising process of Eq. ( EQREF5 ) aims to iteratively reduce the impact of these noise terms. In prior research, the crux of inversion is to introduce the appropriate noise INLINEFORM3 at each step to identify a suitable INLINEFORM4 . This allows the model to obtain INLINEFORM5 as the final output after the denoising process. However, iteratively updating INLINEFORM6 can be time-consuming, and when the model lacks high precision, achieving satisfactory results within a reasonable number of iterations may be challenging.

To address this, we propose an alternative perspective. During inversion, rather than searching for better noise, we aggregate the latent state from the last time step INLINEFORM0 with the current latent state INLINEFORM1 at specific time steps INLINEFORM2 , as illustrated in the following formula:

 DISPLAYFORM0 

where INLINEFORM0 is a trade-off parameter, typically set to INLINEFORM1 . The selection of INLINEFORM2 will be discussed in Sec. SECREFU28 . This approach effectively increases the weight INLINEFORM3 in INLINEFORM4 , since:

 DISPLAYFORM0 

Given that INLINEFORM0 , for INLINEFORM1 , it follows that INLINEFORM2 . Consequently, in comparison to INLINEFORM3 , INLINEFORM4 carries a higher proportion of INLINEFORM5 and is, therefore, less susceptible to the influence of noise. Our approach, therefore, accentuates the significance of the initial latent state INLINEFORM6 , which encapsulates the most comprehensive information regarding the original image, within INLINEFORM7 .

We compare our EasyInv over the vanilla DDIM Inversion BIBREF5 , ReNoise BIBREF9 , Pan et al. 's method BIBREF8 (referred to as Fixed-Point Iteration), using SD V1.4 and SD-XL on one NVIDIA GTX 3090 GPU.

For Fixed-Point Iteration BIBREF8 , we re-implemented it using settings from the paper, as the source code is unavailable. We set the data type of all methods to float16 by default to improve efficiency. The inversion and denoising steps INLINEFORM0 , except for Fixed-Point Iteration, which recommends INLINEFORM1 . For our EasyInv, we use INLINEFORM2 and INLINEFORM3 with the SD-XL framework, and INLINEFORM4 and INLINEFORM5 with SD-V1-4, due to the varying capacities of the two models.

For quantitative comparison, we use three major metrics: LPIPS index BIBREF18 , SSIM BIBREF19 , and PSNR. The LPIPS index uses a pre-trained VGG16 BIBREF20 to compare image pairs. SSIM and PSNR measure image similarity. We also report inference time. We randomly sample 2,298 images from the COCO 2017 test and validation sets BIBREF21 . With the well-trained SD-XL model, error accumulation is minimal, making all methods perform similarly. Therefore, we display results using the SD-V1-4 model.

Table TABREF24 presents the quantitative results of different methods. EasyInv achieves a competitive LPIPS score of 0.321, better than ReNoise (0.316) and Fixed-Point Iteration (0.373), indicating closer perceptual similarity to the original image. For SSIM, EasyInv achieves the highest score of 0.646, showing superior structural similarity crucial for maintaining image coherence. For PSNR, EasyInv scores 30.189, close to ReNoise's highest score of 31.025, indicating high image fidelity. EasyInv completes the inversion process in the fastest time of 5 seconds, matching DDIM Inversion, and significantly quicker than ReNoise (16 seconds) and Fixed-Point Iteration (14 seconds), highlighting its efficiency without compromising on quality. In summary, EasyInv performs strongly across all metrics, with the highest SSIM score indicating effective preservation of image structure. Its efficient inversion makes it highly suitable for real-world applications where both quality and speed are crucial.

Table TABREF25 compares EasyInv's performance in half-precision (float16) and full-precision (float32) formats. Both achieve the same LPIPS score of 0.321, indicating consistent perceptual similarity to the original image. Similarly, both achieve an SSIM score of 0.646, showing preserved structural integrity with high fidelity. For PSNR, half precision slightly outperforms full precision with scores of 30.189 and 30.184. This slight advantage in PSNR for half precision is noteworthy given its well reduced computation time. The most significant difference is observed in the time metric, where half precision completes the inversion process in 5 seconds, approximately 44% faster than full precision, which takes 9 seconds. This efficiency gain highlights EasyInv's exceptional optimization for half precision, offering faster speeds and reduced resources without compromising output quality.

We visually evaluate all methods using SD-XL and SD-V1-4. Figure FIGREF26 presents a comparison of several examples across all methods utilizing SD-XL. ReNoise struggles with images containing significant white areas, resulting in black images. The other two methods also perform poorly, especially evident in the clock example. Figure FIGREF27 displays the results obtained from the SD-V1-4 using images sourced from the internet. These images also feature large areas of white color. ReNoise consistently produces black images with these inputs, indicating an issue inherent to the method rather than the model. Fixed-Point Iteration and DDIM Inversion also fail to generate satisfactory results in such cases, suggesting these images pose challenges for inversion methods. Our method, shown in the figure, effectively addresses these challenges, demonstrating robustness and enhancing performance in handling special scenarios. These findings underscore the efficacy of our approach, particularly in addressing challenging cases that are less common in the COCO dataset.

Figure FIGREF29 presents more visual results of our method, with original images exclusively obtained from the COCO dataset BIBREF21 . The results are unequivocal: our approach consistently generates images that closely resemble their originals post-inversion and reconstruction. The variety of categories represented in these images underscores the broad applicability and consistent performance of our method. In aggregate, these findings affirm that our technique is not merely efficient but also remarkably robust, adeptly reconstructing images with a high level of precision and clarity.

To showcase the practical utility of our EasyInv, we have employed various inversion techniques within the realm of consistent image synthesis and editing. We have seamlessly integrated these inversion methods into MasaCtrl BIBREF6 , a widely-adopted image editing approach that extracts correlated local content and textures from source images to ensure consistency. For demonstrative purposes, we present an image of a “peach” alongside the prompt “A football.” The impact of inversion quality is depicted in Figure FIGREF31 . In these instances, we utilize the inverted latents of the “peach” image, as shown in Figure FIGREF27 , as the input for MasaCtrl BIBREF6 . Our ultimate goal is to generate an image of a football that retains the distinctive features of the “peach” image. As evident from Figure FIGREF31 , our EasyInv achieves superior texture quality and a shape most closely resembling that of a football. From our perspective, images with extensive white areas constitute a significant category in actual image editing, given that they are a prevalent characteristic in conventional photography. However, such features often prove detrimental to the ReNoise method. Thus, for authentic image editing scenarios, our approach stands out as a preferable alternative, not to mention its commendable efficiency.

One potential risk associated with our approach is the phenomenon known as “over-denoising,” which occurs when there is a disproportionate focus on achieving a pristine final-step latent state. This can occasionally result in overly smooth image outputs, as exemplified by the “peach” figure in Figure FIGREF27 . In the context of most real-world image editing tasks, this is not typically an issue, as these tasks often involve style migration, which inherently alters the details of the original image. However, in specific applications, such as using diffusion models for creating advertisements, this could pose a challenge. Nonetheless, our experimental results highlight that the method's two key benefits significantly outweigh this minor shortcoming. Firstly, it is capable of delivering satisfactory outcomes even with models that may under-perform relative to other methods, as shown in the above experiments. Secondly, it enhances inversion efficiency by reverting to the original DDIM Inversion baseline BIBREF5 , thereby eliminating the necessity for iterative optimizations. This strategy not only simplifies the process but also ensures the maintenance of high-quality outputs, marking it as a noteworthy advancement over current methodologies.

In conclusion, our research has made significant strides with the introduction of EasyInv. As we look ahead, our commitment to advancing this technology remains unwavering. Our future research agenda will be focused on the persistent enhancement and optimization of the techniques in this paper. This will be done with the ultimate goal of ensuring that our methodology is not only robust and efficient but also highly adaptable to the diverse and ever-evolving needs of industrial applications.

Our EasyInv presents a significant advancement in the field of DDIM Inversion by addressing the inefficiencies and performance limitations in traditional iterative optimization methods. By emphasizing the importance of the initial latent state and introducing a refined strategy for approximating inversion noise, EasyInv enhances both the accuracy efficiency of the inversion process. Our method strategically reinforces the initial latent state's influence, mitigating the impact of noise and ensuring a closer reconstruction to the original image. This approach not only matches but often surpasses the performance of existing DDIM Inversion methods, especially in scenarios with limited model precision or computational resources. EasyInv also demonstrates a remarkable improvement in inference efficiency, achieving approximately three times faster processing than standard iterative techniques. Through extensive evaluations, we have shown that EasyInv consistently delivers high-quality results, making it a robust and efficient solution for image inversion tasks. The simplicity and effectiveness of EasyInv underscore its potential for broader applications, promoting greater accessibility and advancement in the field of diffusion models.

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_hat_result_together_cut.png'))
```  
![](./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_hat_result_together_cut.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_hat_noise_together_cut.png'))
```  
![](./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_hat_noise_together_cut.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_SDXL.png'))
```  
![](./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_SDXL.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_SDV1-4.png'))
```  
![](./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_SDV1-4.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_masa_cut.png'))
```  
![](./temp_dir_arXiv-2408.05159v1.tar.gz/latex/arXiv-2408.05159v1.tar/visual_masa_cut.png)