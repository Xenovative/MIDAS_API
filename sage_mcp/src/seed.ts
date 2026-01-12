import { initDb, addPaper } from './db.js';

const samplePapers = [
  {
    title: 'Attention Is All You Need',
    authors: 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin',
    abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.',
    content: `The Transformer architecture has revolutionized natural language processing and machine learning. Unlike previous sequence-to-sequence models that relied on recurrent neural networks (RNNs) or convolutional neural networks (CNNs), the Transformer uses self-attention mechanisms to process input sequences in parallel.

Key innovations include:
1. Multi-Head Attention: Allows the model to jointly attend to information from different representation subspaces at different positions.
2. Positional Encoding: Since the model contains no recurrence, positional encodings are added to give the model information about the relative or absolute position of tokens.
3. Layer Normalization and Residual Connections: These techniques help with training stability and gradient flow.

The architecture consists of an encoder stack and a decoder stack, each containing multiple identical layers. Each encoder layer has two sub-layers: a multi-head self-attention mechanism and a position-wise fully connected feed-forward network.

Results showed that the Transformer achieved state-of-the-art results on English-to-German and English-to-French translation tasks while requiring significantly less training time than previous models.`,
    publication: 'Advances in Neural Information Processing Systems',
    publication_date: '2017-06-12',
    doi: '10.48550/arXiv.1706.03762',
    url: 'https://arxiv.org/abs/1706.03762',
    topics: 'Machine Learning, Natural Language Processing, Deep Learning',
    keywords: 'transformer, attention mechanism, neural networks, NLP, sequence-to-sequence',
  },
  {
    title: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    authors: 'Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova',
    abstract: 'We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks.',
    content: `BERT (Bidirectional Encoder Representations from Transformers) represents a significant advancement in natural language understanding. The key innovation is the use of bidirectional training of Transformer encoders, allowing the model to learn context from both directions simultaneously.

Pre-training Objectives:
1. Masked Language Model (MLM): Random tokens are masked, and the model learns to predict them based on context from both directions.
2. Next Sentence Prediction (NSP): The model learns to predict whether two sentences appear consecutively in the original text.

Architecture Details:
- BERT-Base: 12 layers, 768 hidden units, 12 attention heads, 110M parameters
- BERT-Large: 24 layers, 1024 hidden units, 16 attention heads, 340M parameters

Fine-tuning Applications:
BERT can be fine-tuned for various downstream tasks including question answering, sentiment analysis, named entity recognition, and text classification. The fine-tuning process typically requires minimal task-specific architecture modifications.

Results demonstrated state-of-the-art performance on 11 NLP tasks, including GLUE benchmark, SQuAD question answering, and SWAG commonsense inference.`,
    publication: 'Proceedings of NAACL-HLT',
    publication_date: '2019-06-04',
    doi: '10.18653/v1/N19-1423',
    url: 'https://arxiv.org/abs/1810.04805',
    topics: 'Machine Learning, Natural Language Processing, Deep Learning',
    keywords: 'BERT, transformers, pre-training, language model, NLP',
  },
  {
    title: 'Deep Residual Learning for Image Recognition',
    authors: 'Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun',
    abstract: 'Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth.',
    content: `ResNet (Residual Networks) introduced skip connections that allow gradients to flow directly through the network, enabling the training of very deep networks (100+ layers) without degradation.

The Core Innovation - Residual Learning:
Instead of learning H(x) directly, the network learns F(x) = H(x) - x, the residual. The original mapping is then H(x) = F(x) + x. This reformulation makes optimization easier because if the identity mapping is optimal, it's easier to push F(x) to zero than to fit an identity mapping with nonlinear layers.

Architecture Variants:
- ResNet-18: 18 layers
- ResNet-34: 34 layers  
- ResNet-50: 50 layers with bottleneck blocks
- ResNet-101: 101 layers
- ResNet-152: 152 layers

Key Results:
1. Won 1st place in ILSVRC 2015 classification task
2. Won 1st place in ILSVRC & COCO 2015 detection and segmentation
3. Demonstrated that deeper networks with residual connections consistently outperform shallower ones

The residual learning principle has since been adopted across many domains including natural language processing, speech recognition, and generative models.`,
    publication: 'IEEE Conference on Computer Vision and Pattern Recognition',
    publication_date: '2016-06-27',
    doi: '10.1109/CVPR.2016.90',
    url: 'https://arxiv.org/abs/1512.03385',
    topics: 'Computer Vision, Deep Learning, Machine Learning',
    keywords: 'ResNet, residual learning, deep learning, image classification, CNN',
  },
  {
    title: 'GPT-4 Technical Report',
    authors: 'OpenAI',
    abstract: 'We report the development of GPT-4, a large-scale, multimodal model which can accept image and text inputs and produce text outputs. While less capable than humans in many real-world scenarios, GPT-4 exhibits human-level performance on various professional and academic benchmarks, including passing a simulated bar exam with a score around the top 10% of test takers.',
    content: `GPT-4 represents a significant milestone in large language model development, demonstrating capabilities across a wide range of domains including reasoning, coding, and multimodal understanding.

Key Capabilities:
1. Multimodal Input: Can process both text and images
2. Extended Context: Supports context windows up to 32K tokens
3. Improved Reasoning: Better performance on complex reasoning tasks
4. Reduced Hallucinations: More factually accurate than previous versions

Benchmark Performance:
- Bar Exam: ~90th percentile
- SAT Math: 700/800
- GRE Quantitative: 163/170
- LSAT: ~88th percentile

Safety and Alignment:
GPT-4 incorporates extensive safety measures including RLHF (Reinforcement Learning from Human Feedback) and red-teaming. The model shows improved refusal of harmful requests while maintaining helpfulness.

Limitations:
- Still prone to hallucinations
- Limited knowledge cutoff
- Can be manipulated through adversarial prompts
- Reasoning errors on novel problems

The model demonstrates emergent capabilities not present in smaller models, suggesting continued scaling may yield further improvements.`,
    publication: 'arXiv preprint',
    publication_date: '2023-03-15',
    doi: '10.48550/arXiv.2303.08774',
    url: 'https://arxiv.org/abs/2303.08774',
    topics: 'Machine Learning, Natural Language Processing, Artificial Intelligence',
    keywords: 'GPT-4, large language model, multimodal, AI safety, benchmarks',
  },
  {
    title: 'ImageNet Classification with Deep Convolutional Neural Networks',
    authors: 'Alex Krizhevsky, Ilya Sutskever, Geoffrey E. Hinton',
    abstract: 'We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest into the 1000 different classes. On the test data, we achieved top-1 and top-5 error rates of 37.5% and 17.0% which is considerably better than the previous state-of-the-art.',
    content: `AlexNet marked the beginning of the deep learning revolution in computer vision, demonstrating that deep convolutional neural networks could dramatically outperform traditional computer vision methods.

Architecture:
- 8 layers: 5 convolutional + 3 fully connected
- 60 million parameters
- ReLU activation functions
- Local Response Normalization
- Overlapping pooling
- Dropout for regularization

Key Innovations:
1. ReLU Activation: Faster training compared to tanh or sigmoid
2. GPU Training: Used two GTX 580 GPUs for parallel training
3. Data Augmentation: Image translations, horizontal reflections, PCA-based color augmentation
4. Dropout: Reduced overfitting in fully connected layers

Training Details:
- Trained on ImageNet LSVRC-2010 dataset (1.2M images, 1000 classes)
- SGD with momentum (0.9)
- Batch size: 128
- Learning rate: 0.01, reduced by factor of 10 when validation error plateaued
- Training time: 5-6 days on two GPUs

Impact:
AlexNet's success sparked the deep learning revolution, leading to rapid advances in computer vision and eventually other domains. The techniques introduced became standard practice in the field.`,
    publication: 'Advances in Neural Information Processing Systems',
    publication_date: '2012-12-03',
    doi: null,
    url: 'https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks',
    topics: 'Computer Vision, Deep Learning, Machine Learning',
    keywords: 'AlexNet, CNN, ImageNet, deep learning, image classification',
  },
  {
    title: 'Generative Adversarial Networks',
    authors: 'Ian J. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, Yoshua Bengio',
    abstract: 'We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.',
    content: `Generative Adversarial Networks (GANs) introduced a novel approach to generative modeling through adversarial training between two neural networks.

The Framework:
- Generator (G): Takes random noise z and produces synthetic data
- Discriminator (D): Distinguishes between real and generated data
- Training: G tries to fool D, while D tries to correctly classify real vs fake

Mathematical Formulation:
min_G max_D V(D,G) = E[log D(x)] + E[log(1 - D(G(z)))]

This minimax game reaches equilibrium when G produces data indistinguishable from real data.

Training Dynamics:
1. Update D to maximize classification accuracy
2. Update G to minimize D's ability to distinguish fake from real
3. Alternate between these updates

Challenges:
- Mode collapse: G produces limited variety
- Training instability: Difficult to balance G and D
- Evaluation metrics: Hard to quantify generation quality

Applications:
- Image synthesis and manipulation
- Super-resolution
- Style transfer
- Data augmentation
- Domain adaptation

GANs have spawned numerous variants including DCGAN, StyleGAN, CycleGAN, and many others, becoming a foundational technique in generative AI.`,
    publication: 'Advances in Neural Information Processing Systems',
    publication_date: '2014-06-10',
    doi: '10.48550/arXiv.1406.2661',
    url: 'https://arxiv.org/abs/1406.2661',
    topics: 'Machine Learning, Deep Learning, Generative Models',
    keywords: 'GAN, generative models, adversarial training, neural networks',
  },
  {
    title: 'A Survey on Large Language Models: Applications, Challenges, and Opportunities',
    authors: 'Wayne Xin Zhao, Kun Zhou, Junyi Li, Tianyi Tang, Xiaolei Wang, Yupeng Hou',
    abstract: 'Large language models (LLMs) have shown remarkable capabilities in natural language understanding and generation. This survey provides a comprehensive overview of LLM applications across various domains, discusses key challenges including hallucination, bias, and computational costs, and identifies future research opportunities.',
    content: `This survey examines the landscape of Large Language Models and their impact across multiple domains.

Applications:
1. Natural Language Processing
   - Text generation and summarization
   - Question answering
   - Machine translation
   - Sentiment analysis

2. Code Generation
   - Program synthesis
   - Code completion
   - Bug detection and fixing
   - Documentation generation

3. Scientific Research
   - Literature review assistance
   - Hypothesis generation
   - Data analysis
   - Paper writing support

4. Education
   - Personalized tutoring
   - Content creation
   - Assessment generation
   - Language learning

Challenges:
1. Hallucination: LLMs generate plausible but incorrect information
2. Bias: Models reflect biases present in training data
3. Computational Cost: Training and inference require significant resources
4. Privacy: Potential leakage of training data
5. Evaluation: Difficulty in comprehensive capability assessment

Future Directions:
- Multimodal integration
- Improved reasoning capabilities
- Efficient fine-tuning methods
- Better alignment with human values
- Domain-specific adaptations

The survey concludes that while LLMs have transformed many fields, significant research is needed to address their limitations and expand their beneficial applications.`,
    publication: 'ACM Computing Surveys',
    publication_date: '2023-09-01',
    doi: '10.1145/3605943',
    url: null,
    topics: 'Natural Language Processing, Machine Learning, Artificial Intelligence',
    keywords: 'large language models, LLM, survey, applications, challenges',
  },
  {
    title: 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
    authors: 'Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela',
    abstract: 'Large pre-trained language models have been shown to store factual knowledge in their parameters, and achieve state-of-the-art results when fine-tuned on downstream NLP tasks. However, their ability to access and precisely manipulate knowledge is still limited. We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG).',
    content: `Retrieval-Augmented Generation (RAG) combines the benefits of retrieval-based and generation-based approaches for knowledge-intensive tasks.

Architecture:
RAG consists of two main components:
1. Retriever: Dense Passage Retrieval (DPR) model that finds relevant documents
2. Generator: BART-based seq2seq model that generates answers conditioned on retrieved documents

Two RAG Variants:
1. RAG-Sequence: Same retrieved documents for entire sequence generation
2. RAG-Token: Different documents can be retrieved for each token

Training:
- End-to-end training of retriever and generator
- Marginalization over retrieved documents
- No direct supervision for retrieval

Key Benefits:
1. Updateable Knowledge: Can update knowledge by modifying document index
2. Interpretability: Can inspect retrieved documents
3. Reduced Hallucination: Grounded in retrieved evidence
4. Efficiency: Smaller models can match larger ones with retrieval

Evaluation Tasks:
- Open-domain question answering
- Fact verification
- Knowledge-intensive dialogue
- Entity linking

Results showed RAG outperforms pure parametric models on knowledge-intensive tasks while providing more interpretable and updateable knowledge access.

This work laid the foundation for modern RAG systems used in production applications.`,
    publication: 'Advances in Neural Information Processing Systems',
    publication_date: '2020-05-22',
    doi: '10.48550/arXiv.2005.11401',
    url: 'https://arxiv.org/abs/2005.11401',
    topics: 'Natural Language Processing, Information Retrieval, Machine Learning',
    keywords: 'RAG, retrieval-augmented generation, knowledge base, question answering',
  },
  {
    title: 'The Quantum Theory of Entanglement and Its Applications',
    authors: 'John Preskill, Michael Nielsen, Isaac Chuang',
    abstract: 'Quantum entanglement is a fundamental resource for quantum information processing. This paper reviews the theoretical foundations of entanglement, its mathematical characterization, and applications in quantum computing, quantum cryptography, and quantum communication.',
    content: `Quantum entanglement represents one of the most profound features of quantum mechanics, with far-reaching implications for information processing.

Fundamentals:
Entanglement occurs when quantum systems cannot be described independently. For a two-qubit system, the Bell states represent maximally entangled states:
|Φ+⟩ = (|00⟩ + |11⟩)/√2
|Φ-⟩ = (|00⟩ - |11⟩)/√2
|Ψ+⟩ = (|01⟩ + |10⟩)/√2
|Ψ-⟩ = (|01⟩ - |10⟩)/√2

Measures of Entanglement:
1. Von Neumann Entropy
2. Entanglement of Formation
3. Concurrence
4. Negativity

Applications:

1. Quantum Computing
   - Quantum gates exploit entanglement for computation
   - Quantum error correction uses entangled states
   - Quantum algorithms achieve speedup through entanglement

2. Quantum Cryptography
   - BB84 and E91 protocols
   - Device-independent quantum key distribution
   - Quantum random number generation

3. Quantum Communication
   - Quantum teleportation
   - Superdense coding
   - Quantum repeaters for long-distance communication

Experimental Progress:
Recent experiments have demonstrated entanglement over 1000+ km using satellite-based quantum communication, paving the way for global quantum networks.

Challenges remain in scaling entangled systems while maintaining coherence, but progress continues rapidly.`,
    publication: 'Reviews of Modern Physics',
    publication_date: '2021-03-15',
    doi: '10.1103/RevModPhys.93.015001',
    url: null,
    topics: 'Quantum Computing, Physics, Quantum Information',
    keywords: 'quantum entanglement, quantum computing, cryptography, Bell states',
  },
  {
    title: 'Climate Change Impacts on Global Food Security: A Systematic Review',
    authors: 'Sarah Chen, Michael Roberts, David Lobell, Wolfram Schlenker',
    abstract: 'Climate change poses significant threats to global food security through impacts on crop yields, water availability, and agricultural systems. This systematic review synthesizes evidence from 500+ studies to assess current understanding and identify knowledge gaps.',
    content: `This comprehensive review examines the multifaceted impacts of climate change on food security across different regions and agricultural systems.

Key Findings:

1. Crop Yield Impacts
   - Global yields projected to decline 2-6% per decade without adaptation
   - Tropical regions face larger negative impacts than temperate zones
   - Wheat, maize, and rice show varying sensitivities to temperature
   - CO2 fertilization provides partial offset but with diminishing returns

2. Water Resources
   - Changing precipitation patterns affect irrigation availability
   - Groundwater depletion accelerating in major agricultural regions
   - Increased drought frequency in Mediterranean and sub-Saharan Africa
   - Flood risks increasing in South and Southeast Asia

3. Regional Variations
   - Sub-Saharan Africa: Most vulnerable, limited adaptive capacity
   - South Asia: High population density compounds risks
   - North America/Europe: Mixed impacts, better adaptation potential
   - Latin America: Coffee and cocoa production particularly threatened

4. Adaptation Strategies
   - Crop breeding for heat and drought tolerance
   - Improved irrigation efficiency
   - Shifting planting dates and locations
   - Diversification of crops and livelihoods

5. Mitigation Co-benefits
   - Sustainable intensification
   - Reduced food waste
   - Dietary shifts toward plant-based foods

Policy Implications:
Investment in agricultural research, climate-smart practices, and social safety nets is critical for maintaining food security under climate change.`,
    publication: 'Nature Climate Change',
    publication_date: '2022-08-10',
    doi: '10.1038/s41558-022-01234-5',
    url: null,
    topics: 'Climate Science, Agriculture, Food Security, Environmental Science',
    keywords: 'climate change, food security, crop yields, adaptation, agriculture',
  },
];

async function seed() {
  console.log('Initializing database...');
  await initDb();
  
  console.log('Seeding sample papers...');
  for (const paper of samplePapers) {
    try {
      const id = addPaper(paper);
      console.log(`Added: ${paper.title} (ID: ${id})`);
    } catch (error) {
      console.error(`Failed to add ${paper.title}:`, error);
    }
  }
  
  console.log('\nSeeding complete! Added', samplePapers.length, 'papers.');
  console.log('\nTopics covered:');
  console.log('- Machine Learning / Deep Learning');
  console.log('- Natural Language Processing');
  console.log('- Computer Vision');
  console.log('- Quantum Computing');
  console.log('- Climate Science');
}

seed().catch(console.error);
