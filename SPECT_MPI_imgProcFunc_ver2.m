function data = SPECT_MPI_imgProcFunc_ver2(img)
% SPECT_MPI_imgProcFunc_ver 2

addpath('./helperFunctions');
img = cc_img(img); % ccimg size = 712x890x3

%% step 1: 3D-registration
% estimation
[~, tforms] = regist_3d(to3d(rgb2gray(img)));

% application (channel by channel)
for ch = 1:3 % R, G and B
    
    % extract image channel by channel
    img_ch = to3d(img(:,:,ch));   
    stress = img_ch(:,:,1:40);
    rest = img_ch(:,:,41:80);
    
    % rest volume is registered to stress volume
    rest(:,:,1:20) = imwarp(rest(:,:,1:20), tforms{1}, 'OutputView', imref3d([89, 89, 20]));
    rest(:,:,21:30) = imwarp(rest(:,:,21:30), tforms{2}, 'OutputView', imref3d([89, 89, 10]));
    rest(:,:,31:40) = imwarp(rest(:,:,31:40), tforms{3}, 'OutputView', imref3d([89, 89, 10]));
    
    % write the registered image to that channel
    img_ch_registed = cat(3, stress, rest);
    img(:,:, ch) = toccimg(img_ch_registed);
end


%% step 2: Get small region mask
mask = get_La_mask(img);

% close
se = strel('diamond', 4); 
mask = imdilate(~mask, se);
mask = ~mask;

% mirror
mask = mask_mirroring(mask);
img(~repmat(mask, [1,1,3])) = 0;

%% output
img = to3d(rgb2gray(img));
data = uint8(cat(4, img(:,:,1:40), img(:,:,41:80))); % ch. 1: stress, ch. 2: rest

end

