



# 

A Text-to-Video Diffusion Model with Expert Transformer


*equal contributions. Core contributors: Zhuoyi, Jiayan, Wendi, Ming, and Shiyu. {yangzy22,tengjy20}@mails.tsinghua.edu.cn, {yuxiaod,jietang}@tsinghua.edu.cn We introduce CogVideoX, a large diffusion transformer model capable of generating videos conditioned on text prompts. It applies a 3D VAE and a 3D transformer based on Expert Adaptive LayerNorm. Employing a progressive training technique, the model is able to generate coherent long-duration videos characterized by significant motion. Additionally, we propose a complete large-scale data processing pipeline, including various data cleaning strategies and video re-caption method, resulting in better generation quality and improved semantic alignment. Finally, CogVideoX achieves state-of-the-art performance across multiple machine metrics and human evaluations.

The rapid development of text-to-video models has been phenomenal, driven by both the Transformer architecture BIBREF0 and diffusion model BIBREF1 . Early attempts to pretrain and scale Transformers to generate videos from text have shown great promise, such as CogVideo BIBREF2 and Phenaki BIBREF3 . Meanwhile, diffusion models have recently made exciting advancements in multimodal generation, including video generation BIBREF4 , BIBREF5 . By using Transformers as the backbone of diffusion models, i.e., Diffusion Transformers (DiT) BIBREF6 , text-to-video generation has reached groundbreaking levels, as evidenced by the impressive Sora showcases BIBREF7 .

Despite these rapid advancements in DiTs, it remains technically unclear how to achieve long-term consistent video generation. Challenges such as efficiently modeling video data, effectively aligning videos with text semantics, as well as constructing the high-quality text-video pairs for model training have thus far been largely unaddressed.

In this work, we train and introduce CogVideoX, a set of large-scale diffusion transformer models designed for generating long-term, temporally consistent videos. We address the challenges mentioned above by developing a 3D variational Autoencoder (VAE), an expert Transformer, and a video data filtering and captioning pipeline, respectively. First, to efficiently consume video data, we design and train a 3D causal VAE that compresses the video along both spatial and temporal dimensions. Compared to unfolding a video into a one-dimensional sequence in the pixel space, this strategy helps significantly reduce the sequence length and associated training compute. Unlike previous video models BIBREF8 that often use a 2D VAE to encode each frame separately, the 3D VAE helps prevent flicker in the generated videos, that is, ensuring continuity among frames.

Second, to improve the alignment between videos and texts, we propose an expert Transformer with expert adaptive LayerNorm to facilitate the fusion between the two modalities. To ensure the temporal consistency in video generation and capture large-scale motions, we propose to use 3D full attention to comprehensively model the video along both temporal and spatial dimensions.

Third, as most video data available online lacks accurate textual descriptions, we develop a video captioning pipeline capable of accurately describing video content. This pipeline is used to generate new textual descriptions for all video data, which significantly enhances CogVideoX's ability to grasp precise semantic understanding.

In addition, we adopt and design progressive training techniques, including mixed-duration training and resolution progressive training, to further enhance the generation performance and stability of CogVideoX. Furthermore, we propose Explicit Uniform Sampling, which stablizes the training loss curve and accelerates convergence by setting different timestep sampling intervals on each data parallel rank.

Both machine and human evaluations suggest that CogVideoX outperforms well-known public models. Figure FIGREF1 shows the performance of CogVideoX in different aspects.

CogVideoX is an ongoing attempt to advance text-to-video generation. To facilitate further developments, we open-source the model weight of part of CogVideoX and the 3D VAE, and we plan to release future and larger models as well. Now open-sourced CogVideoX is capable of generating 720 INLINEFORM0 480 videos of six seconds with eight frames per second. It can be publicly accessed from https://github.com/THUDM/CogVideo.

In the section, we present the CogVideoX model. Figure FIGREF2 illustrates the overall architecture. Given a pair of video and text input, we design a 3D causal VAE to compress the video into the latent space, and the latents are then patchified and unfolded into a long sequence denoted as INLINEFORM0 . Simultaneously, we encode the textual input into text embeddings INLINEFORM1 using T5 BIBREF9 . Subsequently, INLINEFORM2 and INLINEFORM3 are concatenated along the sequence dimension. The concatenated embeddings are then fed into a stack of expert transformer blocks. Finally, the model output are unpatchified to restore the original latent shape, which is then decoded using a 3D causal VAE decoder to reconstruct the video. We illustrate the technical design of the 3D causal VAE and expert transfomer in detail.

Videos encompass not only spatial information but also substantial temporal information, usually resulting in orders of magnitude more data volumes than images. To tackle the computational challenge of modeling video data, we propose to implement a video compression module based on 3D Variational Autoencoders (3D VAEs) BIBREF10 . The idea is to incorporate three-dimentional convolutions to compress videos both spatially and temporally. This can help achieve a higher compression ratio with largely improved quality and continuity of video reconstruction when compared to previous image VAEs BIBREF11 , BIBREF12 .

Figure FIGREF4 (a) shows the structure of the proposed 3D VAE. It comprises an encoder, a decoder and a latent space regularizer. The Gaussian latent space is constrained by a Kullback-Leibler (KL) regularizer. The encoder and decoder consist of four symmetrically arranged stages, respectively performing 2 INLINEFORM0 downsampling and upsampling by the interleaving of ResNet block stacked stages. The first two rounds of downsampling and the last two upsampling involve both the spatial and temporal dimensions, while the last round only applies spatial sampling. This enables the 3D VAE to achieve a 4 INLINEFORM1 compression in the temporal dimension and an 8 INLINEFORM2 8 compression in the spatial dimension. In total, this achieves a 4 INLINEFORM3 8 INLINEFORM4 8 compression from pixels to the latents.

We adopt the temporally causal convolution BIBREF10 , which places all the paddings at the beginning of the convolution space, as shown in Figure FIGREF4 (b). This ensures the future information not to influence the present or past predictions. Given that processing videos with a large number of frames introduces excessive GPU memory usage, we apply context parallel at the temporal dimension for 3D convolution to distribute computation among multiple devices. As illustrated by Figure FIGREF4 (b), due to the causal nature of the convolution, each rank simply sends a segment of length INLINEFORM0 to the next rank, where INLINEFORM1 indicates the temporal kernel size. This results in relatively low communication overhead.

During actual implementation, we first train a 3D VAE on lower resolutions and fewer frames to save computation. We observe that the encoding of larger resolution generalizes naturally, while extending the number of frames to be encoded does not work as seamlessly. Therefore, we conduct a two-stage training process by first training on short videos and finetuning by context parallel on long videos. Both stages of training utilize a weighted combination of the L2 loss, LPIPS BIBREF13 perceptual loss, and GAN loss from a 3D discriminator.

We introduce the design choices in Transformer for CogVideoX, including the patching, positional embedding, and attention strategies for handling the text-video data effectively and efficiently.

The 3D causal VAE encodes a video latent vector of shape INLINEFORM0 , where INLINEFORM1 represents the number of frames, INLINEFORM2 and INLINEFORM3 represent the height and width of each frame, INLINEFORM4 represents the channel number, respectively. The video latents are then patchified along the spatial dimensions, generating sequence INLINEFORM5 of length INLINEFORM6 . Note that, we do not patchify along the temporal dimension in order to enable joint training of images and videos.

Rotary Position Embedding (RoPE) BIBREF14 is a relative positional encoding that has been demonstrated to capture inter-token relationships effectively in LLMs, particularly excelling in modeling long sequences. To adapt to video data, we extend the original RoPE to 3D-RoPE. Each latent in the video tensor can be represented by a 3D coordinate INLINEFORM0 . We independently apply 1D-RoPE to each dimension of the coordinates, each occupying INLINEFORM1 , INLINEFORM2 , and INLINEFORM3 of the hidden states' channel. The resulting encoding is then concatenated along the channel dimension to obtain the final 3D-RoPE encoding.

We empirically examine the use of RoPE. Figure FIGREF8 (a)shows the comparison between 3D RoPE and sinusoidal absolute position encoding. We can observe that the loss curve using 3D RoPE converges significantly faster than that with sinusoidal encoding. We further compare the use of 3D RoPE alone against the combination of 3D RoPE and learnable absolute position embedding. Figure FIGREF8 (b) indicates that the loss curves of both methods converge almost identically. Therefore, we choose to use 3D RoPE alone for simplicity.

We concatenate the embeddings of both text and video at the input stage to better align visual and semantic information. However, the feature spaces of these two modalities differ significantly, and their embeddings may even have different numerical scales. To better process them within the same sequence, we employ the Expert Adaptive Layernorm to handle each modality independently. As shown in Figure FIGREF2 , following DiT BIBREF6 , we use the timestep INLINEFORM0 of the diffusion process as the input to the modulation module. Then, the Vision Expert Adaptive Layernorm (Vison Expert AdaLN) and Text Expert Adaptive Layernorm (Text Expert AdaLN) apply this modulation mechanism to the vision hidden states and text hidden states, respectively. This strategy promotes the alignment of feature spaces across two modalities while minimizing additional parameters.

To verify the adoption of Expert Adaptive Layernorm, we experiment with different ways of incorporating experts: expert LayerNorm and MLP, and expert Layernorm only. Our experiments find that adding expert MLP does not effectively accelerate the model's convergence (Cf. Figure FIGREF8 (c)). To reduce the model parameters, we only choose to use Expert Adaptive Layernorm.

Previous works BIBREF4 , BIBREF15 often employ separated spatial and temporal attention to reduce computational complexity and facilitate fine-tuning from text-to-image models. However, as illustrated in Figure FIGREF14 , this separated attention approach requires extensive implicit transmission of visual information, significantly increasing the learning complexity and making it challenging to maintain the consistency of large-movement objects. Considering the great success of long-context training in LLMs BIBREF16 , BIBREF17 , BIBREF18 and the efficiency of FlashAttention BIBREF19 , we propose a 3D text-video hybrid attention mechanism. This mechanism not only achieves better results but can also be easily adapted to various parallel acceleration methods.

We construct a collection of relatively high-quality video clips with text descriptions through video filters and recaption models. After filtering, approximately 35M single-shot clips remain, with each clip averaging about 6 seconds.

Video generation models need to learn the dynamic information of the world, but unfiltered video data is of highly noisy distribution, primarily due to two reasons: First, videos are human-created, and artificial editing may distort the authentic dynamic information; Second, the quality of videos can significantly drop due to issues during filming, such as camera shakes and substandard equipment.

In addition to the intrinsic quality of the videos, we also consider how well the video data supports model training. Videos with minimal dynamic information or lacking connectivity in dynamic aspects are considered detrimental. Consequently, we have developed a set of negative labels, which include:

1.  Editing : Videos that have undergone obvious artificial processing, such as re-editing and special effects, causing degradation of the visual integrity. 

2.  Lack of Motion Connectivity : Video segments with image transitions lacking motion connectivity, commonly seen in videos artificially spliced or edited from images. 

3.  Low Quality : Poorly shot videos with unclear visuals or excessive camera shake. 

4.  Lecture Type : Videos focusing primarily on a person continuously talking with minimal effective motion, such as educational content, lectures, and live-streamed discussions. 

5.  Text Dominated : Videos containing a substantial amount of visible text or primarily focusing on textual content. 

6.  Noisy Screenshots : Noisy videos recorded from phone or computer screens. 

We sample 20,000 video data samples and label the presence of negative tags in each of them. By using these annotations, we train several filters based on video-llama BIBREF20 to screen out low-quality video data.

In addition, we calculate the optical flow scores and image aesthetic scores of all training videos and dynamically adjust the threshold ranges during training to ensure the fluency and aesthetic quality of the generated videos.

Typically, most video data does not come with corresponding descriptive text, so it is necessary to convert the video data into textual descriptions to provide the essential training data for text-to-video models. Currently, there are some video caption datasets available, such as Panda70M BIBREF21 , COCO Caption BIBREF22 , and WebVid BIBREF23 . However, the captions in these datasets are usually very short and fail to describe the video's content comprehensively.

To generate high-quality video caption data, we establish a Dense Video Caption Data Generation pipeline, as detailed in Figure FIGREF25 . The idea is to generate video captions from image captions.

First, we use the Panda70M video captioning model BIBREF21 to generate short captions for the videos. Then, we employ the image recaptioning model CogVLM BIBREF24 used in Stable Diffusion 3 BIBREF25 and CogView3 BIBREF26 to create dense image captions for each of the frames within a video. Subsequently, we use GPT-4 to summarize all the image captions to produce the final video caption. To accelerate the generation from image captions to video captions, we fine-tune a Llama2 model BIBREF27 using the summary data generated by GPT-4 BIBREF28 , enabling large-scale video caption data generation. Additional details regarding the video caption data generation process can be found in Appendix .

The pipeline above generates the caption data that is used to trained the CogVideoX model introduced in this report. To further accelerate video recaptioning, we also fine-tune an end-to-end video understanding model CogVLM2-Caption, based on the CogVLM2-Video FOOTREF26 and Llama3 BIBREF16 , by using the dense caption data generated from the aforementioned pipeline. The video caption data generated by CogVLM2-Caption is used to train the next generation of CogVideoX. Examples of video captions generated by this end-to-end CogVLM2-Caption model are shown in Appendix . In Appendix , we also present some examples of video generation where a video is first input into CogVLM2-Caption to generate captions, which are then used as input for CogVideoX to generate new videos, effectively achieving video-to-video generation.

We mix images and videos during training, treating each image as a single-frame video. Additionally, we employ progressive training from the resolution perspective. For the diffusion setting, we adopt v-prediction BIBREF29 and zero SNR BIBREF30 , following the noise schedule used in LDM BIBREF11 . During diffusion training for timestep sampling, we also employ an explicit uniform timestep sampling method, which benefits training stability.

Previous video training methods often involve joint training of images and videos with fixed number of frames BIBREF4 , BIBREF8 . However, this approach usually leads to two issues: First, there is a significant gap between the two input types using bidirectional attention, with images having one frame while videos having dozens of frames. We observe that models trained this way tend to diverge into two generative modes based on the token count and not to have good generalizations. Second, to train with a fixed duration, we have to discard short videos and truncate long videos, which prevents full utilization of the videos of varying number of frames.

To address these issues, we choose mixed-duration training, which means training videos of different lengths together. However, inconsistent data shapes within the batch make training difficult. Inspired by Patch'n Pack BIBREF31 , we place videos of different lengths into the same batch to ensure consistent shapes within each batch, a method we refer to as Frame Pack . The process is illustrated in Figure FIGREF27 .

The training pipeline of CogVideoX is divided into three stages: low-resolution training, high-resolution training, and high-quality video fine-tuning. Similar to images, videos from the Internet usually include a significant amount of low-resolution ones. Progressive training can effectively utilize videos of various resolutions. Moreover, training at low resolution initially can equip the model with coarse-grained modeling capabilities, followed by high-resolution training to enhance its ability to capture fine details. Compared to direct high-resolution training, staged training can also help reduce the overall training time.

When adapting low-resolution position encoding to high-resolution, we consider two different methods: interpolation and extrapolation. We show the effects of two methods in Figure FIGREF30 . Interpolation tens to preserve global information more effectively, whereas the extrapolation better retains local details. Given that RoPE is a relative position encoding, We chose the extrapolation to maintain the relative position between pixels.

Since the filtered pre-training data still contains a certain proportion of dirty data, such as subtitles, watermarks, and low-bitrate videos, we selected a subset of higher quality video data, accounting for 20% of the total dataset, for fine-tuning in the final stage. This step effectively removed generated subtitles and watermarks and slightly improved the visual quality. However, we also observed a slight degradation in the model's semantic ability.

 BIBREF1 defines the training objective of diffusion as

 DISPLAYFORM0 

where INLINEFORM0 is uniformly distributed between 1 and T. The common practice is for each rank in the data parallel group to uniformly sample a value between 1 and INLINEFORM1 , which is in theory equivalent to Equation EQREF34 . However, in practice, the results obtained from such random sampling are often not sufficiently uniform, and since the magnitude of the diffusion loss is related to the timesteps, this can lead to significant fluctuations in the loss. Thus, we propose to use Explicit Uniform Sampling to divide the range from 1 to INLINEFORM2 into INLINEFORM3 intervals, where INLINEFORM4 is the number of ranks. Each rank then uniformly samples within its respective interval. This method ensures a more uniform distribution of timesteps. As shown in Figure FIGREF8 (d), the loss curve from training with Explicit Uniform Sampling is noticeably more stable.

In addition, we compare the loss at each diffusion timestep alone between the two methods for a more precise comparison. We find that after using explicit uniform sampling, the loss at all timesteps decreased faster, indicating that this method can accelerate loss convergence.

We conducted ablation studies on some of the designs mentioned in Section SECREF2 to verify their effectiveness.

First, we compared 3D RoPE with sinusoidal absolute position encoding. As shown in Figure , the loss curve using 3D RoPE converges significantly faster than that with sinusoidal encoding. Then we compared the use of 3D RoPE alone with the combination of 3D RoPE and learnable absolute position embedding. As shown in Figure , the loss curves of both methods converge almost identically. For simplicity, we chose to use 3D RoPE alone.

We experimented with different ways of incorporating experts: expert LayerNorm and MLP, and expert Layernorm only. Our experiments found that adding expert MLP does not effectively accelerate the model's convergence (Figure ). To reduce the model parameters, we only chose to use expert adaptive Layernorm.

In this section, we present the performance of CogVideoX through two primary methods: automated metric evaluation and human assessment . We train the CogVideoX models with different parameter sizes. We show results for 2B and 5B for now, larger models are still in training.

To facilitate the development of text-to-video generation, we open-source the model weight at https://github.com/THUDM/CogVideo.

We choose openly-accessible top-performing text-to-video models as baselines, including T2V-Turbo BIBREF32 , AnimateDiff BIBREF15 , VideoCrafter2 BIBREF33 , OpenSora BIBREF34 , Show-1 BIBREF35 , Gen-2 BIBREF36 , Pika BIBREF37 , and LaVie-2 BIBREF38 .

To evaluate the text-to-video generation, we employed several metrics from VBench BIBREF39 : Human Action , Scene , Dynamic Degree , Multiple Objects , and Appearance Style . VBench is a suite of tools designed to automatically assess the quality of generated videos. We have selected certain metrics from VBench, excluding others that do not align with our evaluation needs. For example, the color metric, intended to measure the presence of objects corresponding to specific colors across frames in the generated video, assesses the model's quality by calculating the probability. However, this metric may mislead video generation models that exhibit greater variation, thus it is not to include it in our evaluation.

For longer-generated videos, some models might produce videos with minimal changes between frames to obtain higher scores, but these videos lack rich content. Therefore, a metric for evaluating the dynamism of the video becomes more important. To address this, we employ two video evaluation tools: Dynamic Quality from Devil BIBREF40 and GPT4o-MTScore from ChronoMagic BIBREF41 , which focus more on the dynamic characteristics of videos. Dynamic Quality is defined by the integration of various quality metrics with dynamic scores, mitigating biases arising from negative correlations between video dynamics and video quality. ChronoMagic, for instance, introduces GPT4o-MTScore, a metric designed to measure the metamorphic amplitude of time-lapse videos, such as those depicting physical, biological, and meteorological changes. This metric using GPT-4o BIBREF42 to score the degree of change, providing a fine-grained assessment of video dynamism.

Table TABREF43 provides the performance comparison of CogVideoX and other models. CogVideoX achieves the best performance in five out of the seven metrics and shows competitive results in the remaining two metrics. These results demonstrate that the model not only excels in video generation quality but also outperforms previous models in handling various complex dynamic scenes. In addition, Figure FIGREF1 presents a radar chart that visually illustrates the performance advantages of CogVideoX.

In addition to automated scoring mechanisms, a comparative analysis between the Kling BIBREF43 and CogVideoX is conducted with manual evaluation. One hundred meticulously crafted prompts are used for human evaluators, characterized by their broad distribution, clear articulation, and well-defined conceptual scope. We randomize videos for blind evalution. A panel of evaluators is instructed to assign scores for each detail on a scale from zero to one, with the overall total score rated on a scale from 0 to 5, where higher scores reflect better video quality. To better complement automated evaluation, human evaluation emphasizes the instruction-following capability: the total score cannot exceed 2 if the generated video fails to follow the instruction.

The results shown in Table TABREF45 indicate that CogVideoX wins the human preference over Kling across all aspects. More details about human evaluation are shown in Appendix .

We would like to thank all the data annotators, infra operating staffs, collaborators, and partners as well as everyone at Zhipu AI and Tsinghua University not explicitly mentioned in the report who have provided support, feedback, and contributed to CogVideoX. We would also like to greatly thank BiliBili for data support.

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/bench_eval9.png'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/bench_eval9.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/transformer.png'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/transformer.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/3dvae_combined.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/3dvae_combined.jpg)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/attention.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/attention.jpg)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/pipeline.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/pipeline.jpg)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/CogVideoX.png'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/CogVideoX.png)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/ive.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/ive.jpg)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/t2v/goodcase1.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/t2v/goodcase1.jpg)

```
mdFile.new_line(mdFile.new_inline_image(text='', path='./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/t2v/goodcase2.jpg'))
```  
![](./temp_dir_arXiv-2408.06072v1.tar.gz/latex/arXiv-2408.06072v1.tar/images/t2v/goodcase2.jpg)